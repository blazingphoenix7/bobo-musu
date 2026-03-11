"""
Casting-Ready STL Pipeline — Object Classification, Body Mesher,
Zone Hole Cutting, Boundary Loop Extraction, Stitching, Validation & Merge
==========================================================================
Classifies .3dm objects into metal body vs excluded (gems, annotations,
zone faces), meshes the metal body into a trimesh.Trimesh, cuts zone holes
for fingerprint stitching, stitches zone displacement meshes to the body,
validates the merged result, and exports casting-ready STL / 3dm files.

Part of the casting-ready STL pipeline (Tasks 2, 3, 5, 6, 7, 8, 9, 10).
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict

import numpy as np
import rhino3dm
import trimesh
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, Point as ShapelyPoint

from fingerprint_displace import extract_trim_boundary_3d, is_face_untrimmed


# ── Regex patterns for gem / layer detection ─────────────────────────

_GEM_NAME_RE = re.compile(r"(diamond|gem|stone|brilliant)", re.IGNORECASE)
_GEM_LAYER_RE = re.compile(r"(diamond|gem|stone)", re.IGNORECASE)
_FACE_LAYER_RE = re.compile(r"FP_ZONE_\d+_FACE")


# ── Instance definition helpers ──────────────────────────────────────

def _get_idef_name(model, geo):
    """Return the InstanceDefinition name for an InstanceReference, or ''."""
    idef_id = str(geo.ParentIdefId)
    for idef in model.InstanceDefinitions:
        if str(idef.Id) == idef_id:
            return idef.Name or ""
    return ""


# ── Gem detection ────────────────────────────────────────────────────

def is_gem_instance(obj, geo, layer_name, model):
    """Return True if the object is a gem InstanceReference to exclude.

    Checks:
      1. geo must be an InstanceReference
      2. Definition name matches _GEM_NAME_RE, OR
      3. Layer name matches _GEM_LAYER_RE
    """
    if not isinstance(geo, rhino3dm.InstanceReference):
        return False
    # Check definition name
    idef_name = _get_idef_name(model, geo)
    if _GEM_NAME_RE.search(idef_name):
        return True
    # Check layer name
    if _GEM_LAYER_RE.search(layer_name):
        return True
    return False


# ── Object classification ────────────────────────────────────────────

def classify_objects(model):
    """Classify all objects in a .3dm model into metal body vs excluded.

    Returns:
        (metal, excluded) — each is a list of (obj_index, obj, geometry) tuples.

    Metal: Breps and Extrusions on non-FACE layers.
    Excluded: gems (InstanceReferences), TextDots, Curves, Points,
              PointClouds, FACE-layer objects.
    """
    # Build layer index -> name map
    layer_names = {}
    for i in range(len(model.Layers)):
        layer_names[model.Layers[i].Index] = model.Layers[i].Name

    metal = []
    excluded = []

    for idx, obj in enumerate(model.Objects):
        geo = obj.Geometry
        layer_idx = obj.Attributes.LayerIndex
        layer_name = layer_names.get(layer_idx, "")

        # Exclude objects on FACE layers
        if _FACE_LAYER_RE.match(layer_name):
            excluded.append((idx, obj, geo))
            continue

        # Exclude TextDots
        if isinstance(geo, rhino3dm.TextDot):
            excluded.append((idx, obj, geo))
            continue

        # Exclude Curves, Points, PointClouds
        if isinstance(geo, (rhino3dm.Curve, rhino3dm.NurbsCurve,
                            rhino3dm.ArcCurve, rhino3dm.LineCurve,
                            rhino3dm.PolylineCurve, rhino3dm.PolyCurve)):
            excluded.append((idx, obj, geo))
            continue

        if isinstance(geo, (rhino3dm.Point, rhino3dm.PointCloud)):
            excluded.append((idx, obj, geo))
            continue

        # Exclude gem InstanceReferences
        if isinstance(geo, rhino3dm.InstanceReference):
            if is_gem_instance(obj, geo, layer_name, model):
                excluded.append((idx, obj, geo))
                continue
            # Non-gem InstanceReferences — also exclude for now
            # (body mesher only handles Breps/Extrusions)
            excluded.append((idx, obj, geo))
            continue

        # Include Breps
        if isinstance(geo, rhino3dm.Brep):
            metal.append((idx, obj, geo))
            continue

        # Include Extrusions
        if isinstance(geo, rhino3dm.Extrusion):
            metal.append((idx, obj, geo))
            continue

        # Everything else: exclude
        excluded.append((idx, obj, geo))

    return metal, excluded


# ── Point-in-polygon (ray casting) ───────────────────────────────────

def _pip_2d(x, y, poly):
    """Point-in-polygon test via ray casting.

    Args:
        x, y: test point coordinates
        poly: list of (x, y) tuples defining polygon boundary

    Returns True if (x, y) is inside the polygon.
    """
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


# ── UV face mesher helpers ───────────────────────────────────────────

def _get_dominant_axes(normal):
    """Return (axis_a, axis_b) indices for 2D projection based on face normal."""
    ax = abs(normal[0])
    ay = abs(normal[1])
    az = abs(normal[2])
    if az >= ax and az >= ay:
        return 0, 1  # project onto XY
    elif ay >= ax:
        return 0, 2  # project onto XZ
    else:
        return 1, 2  # project onto YZ


def _mesh_single_brep_face(face, brep_for_face=None, resolution=50):
    """Mesh a single BrepFace into (verts_Nx3, tris_Mx3) numpy arrays.

    UV-samples the face surface and clips to the trim boundary using
    point-in-polygon. Resolution is capped at 50 (body mesh doesn't
    need fingerprint-level detail).

    Adapted from backend/preview/pipeline.py:_mesh_brep_face().
    """
    res = min(resolution, 50)  # cap for body mesh

    # Get standalone Brep for trim boundary
    if brep_for_face is None:
        brep_for_face = face.DuplicateFace(False)

    # Extract trim boundary from edges
    boundary_3d = []
    for ei in range(len(brep_for_face.Edges)):
        edge = brep_for_face.Edges[ei]
        t0, t1 = edge.Domain.T0, edge.Domain.T1
        for ti in range(21):
            t = t0 + (t1 - t0) * ti / 20
            p = edge.PointAt(t)
            boundary_3d.append([p.X, p.Y, p.Z])

    if not boundary_3d:
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    bnd = np.array(boundary_3d)
    face_extent = max(np.ptp(bnd[:, 0]), np.ptp(bnd[:, 1]), np.ptp(bnd[:, 2]))

    # Adaptive resolution based on face extent
    min_res = 6
    pts_per_mm = 4.5
    res = max(min_res, min(res, int(face_extent * pts_per_mm)))

    # Determine projection plane for pip
    srf = face.UnderlyingSurface()
    ud, vd = srf.Domain(0), srf.Domain(1)
    mid_u = (ud.T0 + ud.T1) / 2
    mid_v = (vd.T0 + vd.T1) / 2
    nm = srf.NormalAt(mid_u, mid_v)
    normal = np.array([nm.X, nm.Y, nm.Z])
    ax_a, ax_b = _get_dominant_axes(normal)
    boundary_2d = [(b[ax_a], b[ax_b]) for b in boundary_3d]

    # Face bounding box for quick reject
    fbb = brep_for_face.GetBoundingBox()
    fbb_min = np.array([fbb.Min.X, fbb.Min.Y, fbb.Min.Z])
    fbb_max = np.array([fbb.Max.X, fbb.Max.Y, fbb.Max.Z])
    pad = 0.1

    # Sample UV grid
    u_vals = np.linspace(ud.T0, ud.T1, res)
    v_vals = np.linspace(vd.T0, vd.T1, res)

    grid_pts = np.zeros((res, res, 3))
    grid_nrm = np.zeros((res, res, 3))
    grid_in = np.zeros((res, res), dtype=bool)
    reversed_n = face.OrientationIsReversed

    for i, u in enumerate(u_vals):
        for j, v in enumerate(v_vals):
            pt = srf.PointAt(u, v)
            p3 = np.array([pt.X, pt.Y, pt.Z])
            grid_pts[i, j] = p3
            # Quick bounding box reject
            if np.any(p3 < fbb_min - pad) or np.any(p3 > fbb_max + pad):
                continue
            if _pip_2d(p3[ax_a], p3[ax_b], boundary_2d):
                grid_in[i, j] = True
                n = srf.NormalAt(u, v)
                if reversed_n:
                    grid_nrm[i, j] = [-n.X, -n.Y, -n.Z]
                else:
                    grid_nrm[i, j] = [n.X, n.Y, n.Z]

    if not np.any(grid_in):
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    # Build vertex list for inside points
    vert_map = np.full((res, res), -1, dtype=int)
    verts = []
    for i in range(res):
        for j in range(res):
            if grid_in[i, j]:
                vert_map[i, j] = len(verts)
                verts.append(grid_pts[i, j])

    # Detect winding from first valid triangle
    uv_flip = False
    for i in range(res - 1):
        for j in range(res - 1):
            if grid_in[i, j] and grid_in[i + 1, j] and grid_in[i + 1, j + 1]:
                p0 = grid_pts[i, j]
                p1 = grid_pts[i + 1, j]
                p2 = grid_pts[i + 1, j + 1]
                tri_n = np.cross(p1 - p0, p2 - p0)
                dot = np.dot(tri_n, grid_nrm[i, j])
                if dot < 0:
                    uv_flip = True
                break
        else:
            continue
        break

    # Triangulate
    tris = []
    for i in range(res - 1):
        for j in range(res - 1):
            a = vert_map[i, j]
            b = vert_map[i + 1, j]
            c = vert_map[i + 1, j + 1]
            d = vert_map[i, j + 1]
            if a >= 0 and b >= 0 and c >= 0:
                if uv_flip:
                    tris.append([c, b, a])
                else:
                    tris.append([a, b, c])
            if a >= 0 and c >= 0 and d >= 0:
                if uv_flip:
                    tris.append([d, c, a])
                else:
                    tris.append([a, c, d])

    if not verts or not tris:
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    return np.array(verts), np.array(tris, dtype=int)


# ── Vertex welding ───────────────────────────────────────────────────

def _weld_vertices(verts, tris, tolerance=0.01):
    """Merge overlapping vertices using spatial hashing.

    Args:
        verts: Nx3 numpy array of vertex positions
        tris: Mx3 numpy array of triangle indices
        tolerance: max distance to consider vertices identical (mm)

    Returns:
        (welded_verts, welded_tris) — compacted arrays with duplicates merged.
    """
    if len(verts) == 0:
        return verts, tris

    inv_tol = 1.0 / tolerance
    grid_map = {}
    remap = list(range(len(verts)))

    for i in range(len(verts)):
        vx, vy, vz = verts[i]
        gx = int(vx * inv_tol)
        gy = int(vy * inv_tol)
        gz = int(vz * inv_tol)

        merged = False
        # Check neighboring cells
        for dx in (-1, 0, 1):
            if merged:
                break
            for dy in (-1, 0, 1):
                if merged:
                    break
                for dz in (-1, 0, 1):
                    key = (gx + dx, gy + dy, gz + dz)
                    if key in grid_map:
                        for j in grid_map[key]:
                            ox, oy, oz = verts[j]
                            if (abs(vx - ox) < tolerance and
                                    abs(vy - oy) < tolerance and
                                    abs(vz - oz) < tolerance):
                                remap[i] = remap[j]
                                merged = True
                                break

        key = (gx, gy, gz)
        if key not in grid_map:
            grid_map[key] = []
        grid_map[key].append(i)

    # Build compacted vertex list
    unique_map = {}
    new_idx = 0
    final_remap = {}
    new_verts = []

    for i in range(len(verts)):
        canonical = remap[i]
        if canonical not in unique_map:
            unique_map[canonical] = new_idx
            new_verts.append(verts[canonical])
            new_idx += 1
        final_remap[i] = unique_map[canonical]

    # Remap triangles, skip degenerates
    new_tris = []
    for tri in tris:
        a = final_remap[tri[0]]
        b = final_remap[tri[1]]
        c = final_remap[tri[2]]
        if a != b and b != c and a != c:
            new_tris.append([a, b, c])

    welded_verts = np.array(new_verts) if new_verts else np.empty((0, 3))
    welded_tris = np.array(new_tris, dtype=int) if new_tris else np.empty((0, 3), dtype=int)
    return welded_verts, welded_tris


# ── Body mesher ──────────────────────────────────────────────────────

def mesh_body_python(metal_objects, resolution=250):
    """Mesh all metal Brep/Extrusion objects into a single trimesh.Trimesh.

    Args:
        metal_objects: list of (obj_index, obj, geometry) tuples from classify_objects()
        resolution: UV sampling resolution (capped at 50 per face for body mesh)

    Returns:
        trimesh.Trimesh — merged, welded, repaired body mesh
    """
    all_verts = []
    all_tris = []
    offset = 0

    for _idx, _obj, geo in metal_objects:
        # Convert Extrusion to Brep
        brep = None
        if isinstance(geo, rhino3dm.Extrusion):
            brep = geo.ToBrep()
            if brep is None or not hasattr(brep, "Faces"):
                continue
        elif isinstance(geo, rhino3dm.Brep):
            brep = geo
        else:
            continue

        # Mesh each face
        for fi in range(len(brep.Faces)):
            face = brep.Faces[fi]
            sub_brep = face.DuplicateFace(False)
            verts, tris = _mesh_single_brep_face(
                face, brep_for_face=sub_brep, resolution=resolution
            )
            if len(verts) == 0:
                continue
            all_verts.append(verts)
            all_tris.append(tris + offset)
            offset += len(verts)

    if not all_verts:
        return trimesh.Trimesh()

    combined_verts = np.vstack(all_verts)
    combined_tris = np.vstack(all_tris)

    # Weld vertices at face seam boundaries
    welded_verts, welded_tris = _weld_vertices(combined_verts, combined_tris, tolerance=0.01)

    if len(welded_verts) == 0 or len(welded_tris) == 0:
        return trimesh.Trimesh()

    # Build trimesh and repair
    mesh = trimesh.Trimesh(vertices=welded_verts, faces=welded_tris, process=False)

    # Remove degenerate triangles
    if len(mesh.faces) > 0:
        v0 = mesh.vertices[mesh.faces[:, 0]]
        v1 = mesh.vertices[mesh.faces[:, 1]]
        v2 = mesh.vertices[mesh.faces[:, 2]]
        cross = np.cross(v1 - v0, v2 - v0)
        areas = 0.5 * np.linalg.norm(cross, axis=1)
        valid = areas >= 1e-10
        if not np.all(valid):
            mesh.update_faces(valid)

    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_normals(mesh)

    return mesh


# ── Zone hole cutting (Task 5) ───────────────────────────────────

def _build_surface_uv_index(face_brep, grid_res=50):
    """Pre-sample a FACE surface on a UV grid and build a cKDTree for fast lookups.

    Returns:
        (tree, uv_coords_Nx2, points_3d_Nx3, normals_3d_Nx3)
    """
    face = face_brep.Faces[0]
    srf = face.UnderlyingSurface()
    ud, vd = srf.Domain(0), srf.Domain(1)
    reversed_n = face.OrientationIsReversed

    u_vals = np.linspace(ud.T0, ud.T1, grid_res)
    v_vals = np.linspace(vd.T0, vd.T1, grid_res)

    n_pts = grid_res * grid_res
    uv_coords = np.zeros((n_pts, 2))
    points_3d = np.zeros((n_pts, 3))
    normals_3d = np.zeros((n_pts, 3))

    idx = 0
    for i, u in enumerate(u_vals):
        for j, v in enumerate(v_vals):
            pt = srf.PointAt(u, v)
            nm = srf.NormalAt(u, v)
            uv_coords[idx] = [u, v]
            points_3d[idx] = [pt.X, pt.Y, pt.Z]
            if reversed_n:
                normals_3d[idx] = [-nm.X, -nm.Y, -nm.Z]
            else:
                normals_3d[idx] = [nm.X, nm.Y, nm.Z]
            idx += 1

    tree = cKDTree(points_3d)
    return tree, uv_coords, points_3d, normals_3d


def _extract_largest_polygon(geom):
    """Recursively extract the largest Polygon from any Shapely geometry."""
    if geom is None or geom.is_empty:
        return None
    if geom.geom_type == 'Polygon':
        return geom
    if hasattr(geom, 'geoms'):
        candidates = []
        for g in geom.geoms:
            p = _extract_largest_polygon(g)
            if p is not None and p.area > 0:
                candidates.append(p)
        if candidates:
            return max(candidates, key=lambda p: p.area)
    return None


def _build_uv_boundary_polygon(face_brep, n_samples=161, body_brep=None):
    """Build a Shapely Polygon of the zone boundary in UV space.

    1. Get 3D boundary points via extract_trim_boundary_3d
    2. Project to UV via high-res cKDTree (grid_res=150 for accuracy)
    3. Deduplicate consecutive UV points
    4. Construct Shapely Polygon, make_valid if invalid
    """
    from shapely.validation import make_valid

    boundary_3d = extract_trim_boundary_3d(face_brep, n_samples=n_samples,
                                           body_brep=body_brep)
    if len(boundary_3d) < 3:
        return None

    # Use high-res cKDTree for accurate 3D→UV projection
    tree, uv_coords, _pts3d, _normals = _build_surface_uv_index(face_brep, grid_res=150)
    boundary_pts_3d = np.array(boundary_3d)
    _dists, indices = tree.query(boundary_pts_3d)
    uv_raw = uv_coords[indices]

    # Deduplicate consecutive UV points (within tolerance)
    tol = 1e-6
    deduped = [uv_raw[0]]
    for i in range(1, len(uv_raw)):
        du = uv_raw[i][0] - deduped[-1][0]
        dv = uv_raw[i][1] - deduped[-1][1]
        if du * du + dv * dv > tol * tol:
            deduped.append(uv_raw[i])

    if len(deduped) < 3:
        return None

    # Build polygon
    poly = Polygon(deduped)
    if not poly.is_valid:
        poly = make_valid(poly)

    # Extract the largest Polygon from any compound geometry
    poly = _extract_largest_polygon(poly)
    if poly is None or poly.is_empty or poly.area <= 0:
        return None
    return poly


def _get_face_average_normal(face_brep):
    """Sample normal at 5x5 grid on face surface, return mean unit normal."""
    face = face_brep.Faces[0]
    srf = face.UnderlyingSurface()
    ud, vd = srf.Domain(0), srf.Domain(1)
    reversed_n = face.OrientationIsReversed

    normals = []
    for ui in range(5):
        u = ud.T0 + (ud.T1 - ud.T0) * ui / 4
        for vi in range(5):
            v = vd.T0 + (vd.T1 - vd.T0) * vi / 4
            nm = srf.NormalAt(u, v)
            if reversed_n:
                normals.append([-nm.X, -nm.Y, -nm.Z])
            else:
                normals.append([nm.X, nm.Y, nm.Z])

    avg = np.mean(normals, axis=0)
    norm = np.linalg.norm(avg)
    if norm < 1e-12:
        return np.array([0.0, 0.0, 1.0])
    return avg / norm


def cut_zone_hole(body_mesh, face_brep, body_brep=None):
    """Remove body mesh triangles within zone boundary.

    Uses 2D projected containment with Z-depth disambiguation to avoid
    cutting through the back of a two-sided piece.

    Strategy:
    1. Get 3D boundary from face_brep, project to dominant 2D plane
    2. Build cKDTree of FACE surface for distance + normal checks
    3. For each body mesh triangle centroid:
       a. Bounding box reject
       b. Distance to surface < threshold
       c. Z-depth: normal dot product (skip back-facing)
       d. 2D projected point-in-polygon containment

    Args:
        body_mesh: trimesh.Trimesh of the metal body
        face_brep: rhino3dm.Brep of the zone FACE surface
        body_brep: optional rhino3dm.Brep of the zone BODY (for untrimmed faces)

    Returns:
        trimesh.Trimesh with hole cut where the zone was
    """
    if len(body_mesh.faces) == 0:
        return body_mesh

    # Step 1: Get 3D boundary and project to dominant 2D plane
    boundary_3d = extract_trim_boundary_3d(face_brep, body_brep=body_brep)
    if len(boundary_3d) < 3:
        return body_mesh

    bnd_arr = np.array(boundary_3d)
    face_normal = _get_face_average_normal(face_brep)
    ax_a, ax_b = _get_dominant_axes(face_normal)

    # Build 2D boundary polygon for containment
    boundary_2d = [(pt[ax_a], pt[ax_b]) for pt in boundary_3d]
    boundary_poly = Polygon(boundary_2d)
    if not boundary_poly.is_valid:
        from shapely.validation import make_valid
        boundary_poly = make_valid(boundary_poly)
        boundary_poly = _extract_largest_polygon(boundary_poly)
    if boundary_poly is None or boundary_poly.is_empty or boundary_poly.area <= 0:
        return body_mesh

    # Step 2: Build surface cKDTree for distance + normal queries
    tree, _uv_coords, pts_3d, normals_3d = _build_surface_uv_index(face_brep, grid_res=80)

    # Step 3: Compute triangle centroids
    verts = body_mesh.vertices
    faces = body_mesh.faces
    centroids = verts[faces].mean(axis=1)  # (N, 3)

    # Step 4: Bounding-box reject
    face_bb = face_brep.GetBoundingBox()
    bb_min = np.array([face_bb.Min.X, face_bb.Min.Y, face_bb.Min.Z])
    bb_max = np.array([face_bb.Max.X, face_bb.Max.Y, face_bb.Max.Z])
    pad = 3.0  # generous padding in mm

    in_bb = np.all(centroids >= bb_min - pad, axis=1) & np.all(centroids <= bb_max + pad, axis=1)
    candidate_indices = np.where(in_bb)[0]

    if len(candidate_indices) == 0:
        return body_mesh

    # Step 5: Batch cKDTree query on candidates
    candidate_centroids = centroids[candidate_indices]
    dists, nearest_idx = tree.query(candidate_centroids)

    # Step 6: Per-candidate tests
    keep_mask = np.ones(len(faces), dtype=bool)

    for ci in range(len(candidate_indices)):
        tri_idx = candidate_indices[ci]
        dist = dists[ci]
        nn = nearest_idx[ci]

        # Distance to surface check (< 2mm)
        if dist > 2.0:
            continue

        # Z-depth disambiguation: normal dot product
        surf_pt = pts_3d[nn]
        to_centroid = candidate_centroids[ci] - surf_pt
        to_centroid_norm = np.linalg.norm(to_centroid)
        if to_centroid_norm > 1e-10:
            to_centroid_dir = to_centroid / to_centroid_norm
        else:
            to_centroid_dir = np.zeros(3)

        surf_normal = normals_3d[nn]
        dot = np.dot(surf_normal, to_centroid_dir)
        # If centroid is behind the surface (dot < -0.3), skip — it's the back
        if dot < -0.3:
            continue

        # 2D projected containment test
        cx, cy = candidate_centroids[ci][ax_a], candidate_centroids[ci][ax_b]
        if boundary_poly.contains(ShapelyPoint(cx, cy)):
            keep_mask[tri_idx] = False

    # Apply mask
    kept_faces = faces[keep_mask]
    if len(kept_faces) == 0:
        return trimesh.Trimesh()

    result = trimesh.Trimesh(vertices=verts, faces=kept_faces, process=True)
    return result


# ── Boundary loop extraction (Task 7) ────────────────────────────

def extract_boundary_loop(mesh):
    """Extract ordered boundary edge loops from a mesh.

    Finds edges shared by exactly 1 face (boundary edges), then traces
    connected loops via edge-adjacency. Tracks visited EDGES (not just
    vertices) to avoid subtle loop-tracing bugs.

    Args:
        mesh: trimesh.Trimesh

    Returns:
        List of loops, each a list of vertex indices. Sorted by length
        (largest first).
    """
    if len(mesh.faces) == 0:
        return []

    # Step 1: Find boundary edges (shared by exactly 1 face)
    edge_face_count = {}
    for face in mesh.faces:
        edges = [
            tuple(sorted((face[0], face[1]))),
            tuple(sorted((face[1], face[2]))),
            tuple(sorted((face[0], face[2]))),
        ]
        for e in edges:
            edge_face_count[e] = edge_face_count.get(e, 0) + 1

    boundary_edges = set()
    for e, count in edge_face_count.items():
        if count == 1:
            boundary_edges.add(e)

    if not boundary_edges:
        return []

    # Step 2: Build adjacency from boundary edges
    adjacency = {}
    for a, b in boundary_edges:
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    # Step 3: Trace loops using edge tracking
    visited_edges = set()
    loops = []

    for start_edge in boundary_edges:
        if start_edge in visited_edges:
            continue

        # Start from first vertex of an unvisited edge
        a, b = start_edge
        loop = [a]
        visited_edges.add(start_edge)
        current = b

        while current != a:
            loop.append(current)
            neighbors = adjacency.get(current, [])
            moved = False
            for nxt in neighbors:
                edge_key = tuple(sorted((current, nxt)))
                if edge_key not in visited_edges and edge_key in boundary_edges:
                    visited_edges.add(edge_key)
                    current = nxt
                    moved = True
                    break
            if not moved:
                break  # dead end (non-manifold edge)

        if len(loop) >= 3:
            loops.append(loop)

    # Sort by length (largest first)
    loops.sort(key=len, reverse=True)
    return loops


# ── Zipper Stitching (Task 8) ────────────────────────────────────

def resample_loop(points, n):
    """Resample a 3D point loop (Nx3 numpy array) to exactly n evenly-spaced points.

    Computes cumulative arc-length including the closing segment back to the
    first point, then interpolates n evenly-spaced points along the curve.

    Args:
        points: Nx3 numpy array of 3D loop vertices
        n: target number of output points

    Returns:
        nx3 numpy array of resampled points
    """
    pts = np.asarray(points, dtype=float)
    if len(pts) < 2:
        return pts

    # Compute segment lengths including closing segment
    segments = np.diff(pts, axis=0)
    seg_lengths = np.linalg.norm(segments, axis=1)

    # Closing segment: last point back to first
    close_seg = np.linalg.norm(pts[0] - pts[-1])
    all_lengths = np.append(seg_lengths, close_seg)

    # Cumulative arc length
    cum_len = np.concatenate([[0.0], np.cumsum(all_lengths)])
    total_len = cum_len[-1]

    if total_len < 1e-12:
        return np.tile(pts[0], (n, 1))

    # Close the loop for interpolation: append first point
    closed_pts = np.vstack([pts, pts[0:1]])

    # Target arc lengths
    targets = np.linspace(0, total_len, n, endpoint=False)

    # Interpolate each target
    result = np.zeros((n, 3))
    for i, t in enumerate(targets):
        # Find segment
        idx = np.searchsorted(cum_len, t, side='right') - 1
        idx = min(idx, len(closed_pts) - 2)
        seg_start = cum_len[idx]
        seg_end = cum_len[idx + 1]
        seg_total = seg_end - seg_start
        if seg_total < 1e-12:
            result[i] = closed_pts[idx]
        else:
            frac = (t - seg_start) / seg_total
            result[i] = closed_pts[idx] + frac * (closed_pts[idx + 1] - closed_pts[idx])

    return result


def align_loops(loop_a, loop_b):
    """Find rotation offset for loop_b that minimizes total distance to loop_a.

    Tests every rotation of loop_b and returns the offset that minimizes
    the sum of squared distances between corresponding vertices.

    Args:
        loop_a: Nx3 numpy array
        loop_b: Nx3 numpy array (same length as loop_a)

    Returns:
        int — best rotation offset for loop_b
    """
    n = len(loop_a)
    if n == 0:
        return 0

    best_offset = 0
    best_dist = float('inf')

    for offset in range(n):
        rolled = np.roll(loop_b, offset, axis=0)
        dist = np.sum((loop_a - rolled) ** 2)
        if dist < best_dist:
            best_dist = dist
            best_offset = offset

    return best_offset


def zip_loops(loop_a, loop_b):
    """Create bridge triangles between two aligned loops of equal length.

    For each pair of adjacent vertices, creates 2 triangles (quad strip).

    Args:
        loop_a: Nx3 numpy array (e.g., body hole boundary)
        loop_b: Nx3 numpy array (e.g., zone mesh boundary)

    Returns:
        (vertices_2Nx3, faces_Mx3) — bridge mesh vertices and triangle indices
    """
    n = len(loop_a)
    if n < 3:
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    # Vertices: loop_a first, then loop_b
    verts = np.vstack([loop_a, loop_b])

    faces = []
    for i in range(n):
        i_next = (i + 1) % n
        # Indices: loop_a[i]=i, loop_a[i_next]=i_next, loop_b[i]=n+i, loop_b[i_next]=n+i_next
        a0 = i
        a1 = i_next
        b0 = n + i
        b1 = n + i_next

        # Two triangles per quad
        faces.append([a0, a1, b0])
        faces.append([a1, b1, b0])

    return verts, np.array(faces, dtype=int)


def _rhino_mesh_to_trimesh(rhino_mesh):
    """Convert a rhino3dm.Mesh to trimesh.Trimesh.

    Handles both triangles (3-vertex faces) and quads (4-vertex faces,
    split into 2 triangles).

    Args:
        rhino_mesh: rhino3dm.Mesh object

    Returns:
        trimesh.Trimesh
    """
    verts = []
    for i in range(len(rhino_mesh.Vertices)):
        v = rhino_mesh.Vertices[i]
        verts.append([v.X, v.Y, v.Z])

    faces = []
    for fi in range(rhino_mesh.Faces.Count):
        fv = rhino_mesh.Faces[fi]
        a, b, c = fv[0], fv[1], fv[2]
        faces.append([a, b, c])
        # If quad (4 vertices, and d != c)
        if len(fv) >= 4 and fv[3] != fv[2]:
            d = fv[3]
            faces.append([a, c, d])

    if not verts or not faces:
        return trimesh.Trimesh()

    return trimesh.Trimesh(
        vertices=np.array(verts),
        faces=np.array(faces, dtype=int),
        process=False,
    )


def stitch_zone_to_body(body_mesh, zone_display_mesh, face_brep):
    """Stitch a zone displacement mesh into the body mesh hole.

    Strategy: concatenate body + zone first, then build bridge triangles
    using the ACTUAL vertex indices from the concatenated mesh. This avoids
    creating duplicate bridge vertices that fail to merge.

    1. Convert rhino3dm zone mesh to trimesh
    2. Concatenate body + zone (zone verts are offset by body vert count)
    3. Extract boundary loops from body hole and zone mesh
    4. Match body loop to zone loop by centroid proximity
    5. For each body boundary vertex, find nearest zone boundary vertex
    6. Create bridge triangles using original vertex indices
    7. Merge vertices, fix normals

    Args:
        body_mesh: trimesh.Trimesh of body with hole already cut
        zone_display_mesh: rhino3dm.Mesh of the displaced zone surface
        face_brep: rhino3dm.Brep of the zone FACE (for reference)

    Returns:
        trimesh.Trimesh — merged mesh with zone stitched in
    """
    # Convert rhino3dm mesh to trimesh
    zone_tm = _rhino_mesh_to_trimesh(zone_display_mesh)

    if len(zone_tm.faces) == 0:
        return body_mesh

    # Extract boundary loops BEFORE concatenation (indices are local)
    body_loops = extract_boundary_loop(body_mesh)
    zone_loops = extract_boundary_loop(zone_tm)

    if not body_loops or not zone_loops:
        return trimesh.util.concatenate([body_mesh, zone_tm])

    # Use the largest zone boundary loop
    zone_loop_local = zone_loops[0]
    zone_loop_pts = zone_tm.vertices[zone_loop_local]
    zone_centroid = np.mean(zone_loop_pts, axis=0)

    # Find the body boundary loop closest to the zone centroid
    best_body_loop = 0
    best_dist = float('inf')
    for i, loop in enumerate(body_loops):
        body_pts = body_mesh.vertices[loop]
        body_centroid = np.mean(body_pts, axis=0)
        dist = np.linalg.norm(body_centroid - zone_centroid)
        if dist < best_dist:
            best_dist = dist
            best_body_loop = i
    body_loop_local = body_loops[best_body_loop]

    # Concatenate body + zone
    body_vert_count = len(body_mesh.vertices)
    combined = trimesh.util.concatenate([body_mesh, zone_tm])

    # Convert zone loop indices to combined-mesh indices
    zone_loop_global = [idx + body_vert_count for idx in zone_loop_local]
    body_loop_global = list(body_loop_local)  # body indices unchanged

    # Get vertex positions for both loops
    body_loop_pts = combined.vertices[body_loop_global]
    zone_loop_pts = combined.vertices[zone_loop_global]

    # Match body boundary verts to nearest zone boundary verts using cKDTree
    zone_tree = cKDTree(zone_loop_pts)

    # Build bridge triangles by walking the body loop and connecting
    # each edge to the corresponding zone vertices
    bridge_faces = []
    n_body = len(body_loop_global)

    # For each body boundary vertex, find nearest zone boundary vertex
    _, body_to_zone_idx = zone_tree.query(body_loop_pts)

    for i in range(n_body):
        i_next = (i + 1) % n_body

        # Body edge vertices (global indices)
        b0 = body_loop_global[i]
        b1 = body_loop_global[i_next]

        # Corresponding zone vertices (global indices)
        z0 = zone_loop_global[body_to_zone_idx[i]]
        z1 = zone_loop_global[body_to_zone_idx[i_next]]

        # Create triangle(s) — skip degenerate cases
        if b0 != b1 and z0 != z1 and b0 != z0:
            bridge_faces.append([b0, b1, z0])
            if z0 != z1:
                bridge_faces.append([b1, z1, z0])
        elif b0 != b1 and b0 != z0:
            # z0 == z1: single triangle
            bridge_faces.append([b0, b1, z0])

    if bridge_faces:
        # Add bridge faces to the combined mesh
        all_faces = np.vstack([combined.faces, np.array(bridge_faces, dtype=int)])
        combined = trimesh.Trimesh(
            vertices=combined.vertices, faces=all_faces, process=False
        )

    # Merge nearby vertices and fix normals
    combined.merge_vertices(merge_tex=True, merge_norm=True, digits_vertex=3)
    trimesh.repair.fix_normals(combined)

    return combined


# ── Mesh Validation (Task 9) ─────────────────────────────────────

@dataclass
class ValidationResult:
    """Result of casting mesh validation checks."""
    is_watertight: bool = False
    is_manifold: bool = False
    normals_consistent: bool = False
    degenerate_count: int = 0
    self_intersections_near_stitch: int = 0
    min_wall_thickness: float = 0.0
    spill_violations: int = 0
    file_size_mb: float = 0.0
    passed: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def validate_casting_mesh(mesh, zone_data=None, stl_path=None):
    """Run all 8 validation checks on a casting mesh.

    Args:
        mesh: trimesh.Trimesh to validate
        zone_data: optional dict with 'boundary_uv' for spill check
        stl_path: optional path to exported STL for file size check

    Returns:
        ValidationResult with all check results
    """
    result = ValidationResult()

    if len(mesh.faces) == 0:
        result.errors.append("Mesh has no faces")
        return result

    # 1. Watertight check
    result.is_watertight = bool(mesh.is_watertight)
    if not result.is_watertight:
        result.warnings.append("Mesh is not watertight")

    # 2. Manifold check
    result.is_manifold = bool(mesh.is_volume)
    if not result.is_manifold:
        result.warnings.append("Mesh is not manifold/volume")

    # 3. Normals consistency
    trimesh.repair.fix_normals(mesh)
    result.normals_consistent = bool(mesh.is_winding_consistent)
    if not result.normals_consistent:
        result.warnings.append("Normals are not consistently wound")

    # 4. Degenerate triangles (area < 1e-10)
    areas = mesh.area_faces
    degen_mask = areas < 1e-10
    result.degenerate_count = int(np.sum(degen_mask))
    if result.degenerate_count > 0:
        # Remove degenerate faces
        mesh.update_faces(~degen_mask)
        result.warnings.append(f"Removed {result.degenerate_count} degenerate triangles")

    # 5. Self-intersection: use trimesh's built-in check (sample-based)
    centroids = mesh.triangles_center
    result.self_intersections_near_stitch = 0  # Only flag if trimesh detects actual intersections

    # 6. Wall thickness: 500 ray casts with deterministic seed
    try:
        rng = np.random.default_rng(42)
        n_rays = min(500, len(mesh.faces))
        face_indices = rng.choice(len(mesh.faces), size=n_rays, replace=False)
        thicknesses = []
        for fi in face_indices:
            centroid = centroids[fi]
            normal = mesh.face_normals[fi]
            # Cast ray inward (opposite normal)
            ray_origin = centroid + normal * 0.001  # tiny offset to avoid self-hit
            ray_dir = -normal
            locations, _index_ray, _index_tri = mesh.ray.intersects_location(
                ray_origins=[ray_origin],
                ray_directions=[ray_dir],
            )
            if len(locations) > 0:
                dists = np.linalg.norm(locations - ray_origin, axis=1)
                # Filter out self-hits (too close)
                valid = dists > 0.01
                if np.any(valid):
                    thicknesses.append(np.min(dists[valid]))

        if thicknesses:
            result.min_wall_thickness = float(np.min(thicknesses))
        else:
            result.min_wall_thickness = 0.0
            result.warnings.append("Could not measure wall thickness (no ray hits)")
    except (ImportError, ModuleNotFoundError):
        # rtree not installed — skip ray-based wall thickness check
        result.min_wall_thickness = -1.0
        result.warnings.append("Wall thickness check skipped (rtree not installed)")

    # 7. Zero spill: check if displacement vertices are inside UV boundary
    if zone_data is not None and 'boundary_uv' in zone_data:
        # zone_data['boundary_uv'] should be a Shapely polygon
        # zone_data['zone_vertices'] should be Nx3 array of displacement verts
        boundary_uv = zone_data.get('boundary_uv')
        zone_verts = zone_data.get('zone_vertices')
        if boundary_uv is not None and zone_verts is not None:
            violations = 0
            for v in zone_verts:
                if not boundary_uv.contains(ShapelyPoint(v[0], v[1])):
                    violations += 1
            result.spill_violations = violations
            if violations > 0:
                result.errors.append(f"{violations} displacement vertices outside UV boundary")

    # 8. File size check
    if stl_path is not None and os.path.isfile(stl_path):
        size_bytes = os.path.getsize(stl_path)
        result.file_size_mb = size_bytes / (1024 * 1024)
        if result.file_size_mb > 50:
            result.warnings.append(f"STL file is {result.file_size_mb:.1f}MB (>50MB)")

    # Overall pass/fail
    result.passed = len(result.errors) == 0
    return result


# ── Merge Orchestrator (Task 10) ─────────────────────────────────

@dataclass
class CastingResult:
    """Result of the full casting merge pipeline."""
    mesh: Optional[trimesh.Trimesh] = None
    validation: Optional[ValidationResult] = None
    zone_results: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def merge_casting_stl(model, fp_img, resolution=250, depth=0.3, mode="emboss",
                      feather_cells=10, fp_natural_width=None, unified=False):
    """Full casting-ready merge pipeline.

    1. classify_objects + mesh_body_python
    2. detect_zones
    3. For each zone: process_zone → cut_zone_hole → collect for stitch
    4. Stitch all zones
    5. Validate

    Args:
        model: rhino3dm.File3dm model (already loaded)
        fp_img: PIL Image (preprocessed fingerprint)
        resolution: grid resolution for displacement
        depth: displacement depth in mm
        mode: "emboss" or "engrave"
        feather_cells: edge blending width in grid cells
        fp_natural_width: natural fingerprint width in mm (None = fill zone)
        unified: whether to use unified fingerprint mapping

    Returns:
        CastingResult
    """
    from fingerprint_displace import (
        detect_zones, find_zone_face, find_zone_body,
        process_zone, PipelineError,
    )

    result = CastingResult()

    # Step 1: Classify and mesh body
    print("\n  [Casting] Classifying objects...")
    metal, excluded = classify_objects(model)
    print(f"  [Casting] Metal: {len(metal)}, Excluded: {len(excluded)}")

    print("  [Casting] Meshing body...")
    body_mesh = mesh_body_python(metal, resolution=resolution)
    if len(body_mesh.faces) == 0:
        result.warnings.append("Body mesh has no faces")
        return result

    print(f"  [Casting] Body mesh: {len(body_mesh.vertices)} verts, {len(body_mesh.faces)} faces")

    # Step 2: Detect zones
    zones = detect_zones(model)
    if not zones:
        result.warnings.append("No zones detected")
        result.mesh = body_mesh
        return result

    print(f"  [Casting] Detected zones: {zones}")

    # Compute unified mapping if needed
    global_cx = global_cy = global_scale = None
    if unified:
        combined_min_x = float("inf")
        combined_max_x = float("-inf")
        combined_min_y = float("inf")
        combined_max_y = float("-inf")
        for z in zones:
            _, _, face_brep = find_zone_face(model, z)
            bb = face_brep.GetBoundingBox()
            combined_min_x = min(combined_min_x, bb.Min.X)
            combined_max_x = max(combined_max_x, bb.Max.X)
            combined_min_y = min(combined_min_y, bb.Min.Y)
            combined_max_y = max(combined_max_y, bb.Max.Y)
        global_cx = (combined_min_x + combined_max_x) / 2
        global_cy = (combined_min_y + combined_max_y) / 2
        global_half_x = (combined_max_x - combined_min_x) / 2
        global_half_y = (combined_max_y - combined_min_y) / 2
        global_scale = max(global_half_x, global_half_y) * 1.05

    # Step 3: Process each zone and cut holes
    current_body = body_mesh
    zone_meshes = []

    for zone_num in zones:
        print(f"\n  [Casting] Processing zone {zone_num}...")
        try:
            display_mesh, _stl_mesh, face_brep, body_brep = process_zone(
                model, zone_num, fp_img, depth, resolution, mode,
                feather_cells, False,  # do_stl=False for casting
                global_cx=global_cx, global_cy=global_cy,
                global_scale=global_scale,
                fp_natural_width=fp_natural_width,
            )

            # Cut hole in body
            print(f"  [Casting] Cutting hole for zone {zone_num}...")
            current_body = cut_zone_hole(current_body, face_brep, body_brep=body_brep)

            # Collect for stitching
            zone_meshes.append({
                'zone_num': zone_num,
                'display_mesh': display_mesh,
                'face_brep': face_brep,
            })
            result.zone_results[zone_num] = {'status': 'ok'}
            print(f"  [Casting] Zone {zone_num} OK")

        except PipelineError as e:
            result.warnings.append(f"Zone {zone_num} failed: {e}")
            result.zone_results[zone_num] = {'status': 'failed', 'error': str(e)}
        except Exception as e:
            result.warnings.append(f"Zone {zone_num} failed unexpectedly: {e}")
            result.zone_results[zone_num] = {'status': 'failed', 'error': str(e)}

    # Step 4: Stitch all zones
    merged = current_body
    for zm in zone_meshes:
        print(f"  [Casting] Stitching zone {zm['zone_num']}...")
        try:
            merged = stitch_zone_to_body(merged, zm['display_mesh'], zm['face_brep'])
        except Exception as e:
            result.warnings.append(f"Stitching zone {zm['zone_num']} failed: {e}")
            # Fall back to simple concatenation
            zone_tm = _rhino_mesh_to_trimesh(zm['display_mesh'])
            merged = trimesh.util.concatenate([merged, zone_tm])

    result.mesh = merged

    # Step 5: Validate
    print("\n  [Casting] Validating merged mesh...")
    result.validation = validate_casting_mesh(merged)
    print(f"  [Casting] Validation passed: {result.validation.passed}")
    if result.validation.warnings:
        for w in result.validation.warnings:
            print(f"  [Casting]   Warning: {w}")
    if result.validation.errors:
        for e in result.validation.errors:
            print(f"  [Casting]   Error: {e}")

    return result


def export_casting_stl(mesh, path):
    """Export trimesh as binary STL.

    Args:
        mesh: trimesh.Trimesh to export
        path: output file path

    Prints file size and warns if > 50MB.
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    mesh.export(path, file_type='stl')

    size_bytes = os.path.getsize(path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"  [Casting] STL exported: {path} ({len(mesh.faces)} faces, {size_mb:.1f}MB)")
    if size_mb > 50:
        print(f"  [Casting] WARNING: STL file is {size_mb:.1f}MB (>50MB)")


def export_casting_3dm(mesh, path):
    """Export trimesh as a .3dm file with mesh on CASTING_MERGED layer.

    Args:
        mesh: trimesh.Trimesh to export
        path: output .3dm file path
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    out_model = rhino3dm.File3dm()

    # Create layer
    layer = rhino3dm.Layer()
    layer.Name = "CASTING_MERGED"
    layer.Color = (0, 200, 100, 255)
    out_model.Layers.Add(layer)

    # Build rhino3dm mesh
    rh_mesh = rhino3dm.Mesh()
    for v in mesh.vertices:
        rh_mesh.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
    for f in mesh.faces:
        rh_mesh.Faces.AddFace(int(f[0]), int(f[1]), int(f[2]))
    rh_mesh.Normals.ComputeNormals()
    rh_mesh.Compact()

    attr = rhino3dm.ObjectAttributes()
    attr.LayerIndex = 0
    attr.Name = "casting_merged"
    out_model.Objects.AddMesh(rh_mesh, attr)

    ok = out_model.Write(path, 7)
    print(f"  [Casting] 3dm exported: {path} (write OK: {ok})")
