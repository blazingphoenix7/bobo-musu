"""Thin wrapper around the fingerprint displacement pipeline.

Imports core functions from fingerprint_displace.py and exposes them
in a Django-friendly way (accepts file-like objects, returns bytes).
"""
import re
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
from django.conf import settings

# Add the pipeline directory to sys.path
_PIPELINE_DIR = str(settings.BASE_DIR.parent / "3dm files")
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from fingerprint_displace import (
    preprocess_fingerprint,
    detect_zones,
    process_zone,
    export_stl,
)
import rhino3dm


class PipelineError(Exception):
    """Raised when the displacement pipeline fails."""
    pass


# ── Base mesh extraction (Problem 1) ──────────────────────────────

_base_mesh_cache = {}  # design_path_str -> STL bytes


def _pip(px, py, boundary):
    """Point-in-polygon (ray casting)."""
    n = len(boundary)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = boundary[i]
        xj, yj = boundary[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


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


def _mesh_brep_face(face, brep_for_face=None, min_res=6, max_res=45, pts_per_mm=4.5):
    """Mesh a single BrepFace into (vertices_Nx3, triangles_Mx3) arrays.

    Uses UV sampling + point-in-polygon trimming.
    """
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
    res = max(min_res, min(max_res, int(face_extent * pts_per_mm)))

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
            if _pip(p3[ax_a], p3[ax_b], boundary_2d):
                grid_in[i, j] = True
                n = srf.NormalAt(u, v)
                if reversed_n:
                    grid_nrm[i, j] = [-n.X, -n.Y, -n.Z]
                else:
                    grid_nrm[i, j] = [n.X, n.Y, n.Z]

    if not np.any(grid_in):
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    # Build vertex list for inside points (with normals)
    vert_map = np.full((res, res), -1, dtype=int)
    verts = []
    norms = []
    for i in range(res):
        for j in range(res):
            if grid_in[i, j]:
                vert_map[i, j] = len(verts)
                verts.append(grid_pts[i, j])
                norms.append(grid_nrm[i, j])

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
            a, b, c, d = vert_map[i, j], vert_map[i + 1, j], vert_map[i + 1, j + 1], vert_map[i, j + 1]
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
        return np.empty((0, 3)), np.empty((0, 3)), np.empty((0, 3), dtype=int)

    return np.array(verts), np.array(norms), np.array(tris, dtype=int)


def _mesh_brep(brep, **kwargs):
    """Mesh all faces of a Brep, returning (vertices_Nx3, normals_Nx3, triangles_Mx3)."""
    all_verts = []
    all_norms = []
    all_tris = []
    offset = 0

    for fi in range(len(brep.Faces)):
        face = brep.Faces[fi]
        sub_brep = face.DuplicateFace(False)
        verts, norms, tris = _mesh_brep_face(face, brep_for_face=sub_brep, **kwargs)
        if len(verts) == 0:
            continue
        all_verts.append(verts)
        all_norms.append(norms)
        all_tris.append(tris + offset)
        offset += len(verts)

    if not all_verts:
        return np.empty((0, 3)), np.empty((0, 3)), np.empty((0, 3), dtype=int)
    return np.vstack(all_verts), np.vstack(all_norms), np.vstack(all_tris)


def _apply_transform(verts, xform):
    """Apply a rhino3dm Transform to Nx3 vertices."""
    if len(verts) == 0:
        return verts
    # Build 4x4 matrix
    m = np.array([
        [xform.M00, xform.M01, xform.M02, xform.M03],
        [xform.M10, xform.M11, xform.M12, xform.M13],
        [xform.M20, xform.M21, xform.M22, xform.M23],
        [xform.M30, xform.M31, xform.M32, xform.M33],
    ])
    # Homogeneous coordinates
    ones = np.ones((len(verts), 1))
    pts4 = np.hstack([verts, ones])
    transformed = (m @ pts4.T).T
    # Perspective divide (usually w=1)
    w = transformed[:, 3:4]
    w[w == 0] = 1
    return transformed[:, :3] / w


def _apply_normal_transform(normals, xform):
    """Transform normals using inverse-transpose of upper-left 3x3."""
    if len(normals) == 0:
        return normals
    m3 = np.array([
        [xform.M00, xform.M01, xform.M02],
        [xform.M10, xform.M11, xform.M12],
        [xform.M20, xform.M21, xform.M22],
    ])
    # Normal matrix = inverse-transpose of the 3x3 part
    try:
        normal_mat = np.linalg.inv(m3).T
    except np.linalg.LinAlgError:
        normal_mat = m3  # fallback for singular matrices
    transformed = (normal_mat @ normals.T).T
    # Normalize
    lengths = np.linalg.norm(transformed, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    return transformed / lengths


def _compute_mesh_normals(verts, tris):
    """Compute smooth vertex normals for a mesh by averaging face normals."""
    normals = np.zeros_like(verts)
    v0 = verts[tris[:, 0]]
    v1 = verts[tris[:, 1]]
    v2 = verts[tris[:, 2]]
    face_normals = np.cross(v1 - v0, v2 - v0)
    # Accumulate face normals onto each vertex
    for k in range(3):
        np.add.at(normals, tris[:, k], face_normals)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    lengths[lengths == 0] = 1
    return normals / lengths


def _build_mesh_binary(verts, normals, tris):
    """Build custom binary mesh format with per-vertex normals.

    Format:
        uint32: vertex_count (N)
        uint32: triangle_count (M)
        N*3 float32: positions (x,y,z interleaved)
        N*3 float32: normals (nx,ny,nz interleaved)
        M*3 uint32: indices (i0,i1,i2 interleaved)
    """
    n_verts = len(verts)
    n_tris = len(tris)
    if n_verts == 0 or n_tris == 0:
        return struct.pack("<II", 0, 0)

    buf = bytearray()
    buf.extend(struct.pack("<II", n_verts, n_tris))
    buf.extend(verts.astype(np.float32).tobytes())
    buf.extend(normals.astype(np.float32).tobytes())
    buf.extend(tris.astype(np.uint32).tobytes())
    return bytes(buf)


def _verts_tris_to_stl_bytes(verts, tris):
    """Convert vertex/triangle arrays to binary STL bytes."""
    if len(tris) == 0:
        return b"\0" * 80 + struct.pack("<I", 0)

    # Compute face normals
    v0 = verts[tris[:, 0]]
    v1 = verts[tris[:, 1]]
    v2 = verts[tris[:, 2]]
    e1 = v1 - v0
    e2 = v2 - v0
    normals = np.cross(e1, e2)

    # Filter degenerate triangles
    area2 = np.sum(normals ** 2, axis=1)
    valid = area2 > 1e-20
    normals = normals[valid]
    v0 = v0[valid]
    v1 = v1[valid]
    v2 = v2[valid]

    n_tris = len(normals)
    buf = bytearray(80 + 4 + n_tris * 50)
    struct.pack_into("<I", buf, 80, n_tris)
    for i in range(n_tris):
        off = 84 + i * 50
        struct.pack_into("<fff", buf, off, *normals[i])
        struct.pack_into("<fff", buf, off + 12, *v0[i])
        struct.pack_into("<fff", buf, off + 24, *v1[i])
        struct.pack_into("<fff", buf, off + 36, *v2[i])
        # attribute byte count = 0 (already zeroed)

    return bytes(buf)


def extract_base_mesh(design_path):
    """Extract the full jewelry piece (minus zone faces) as STL bytes.

    Caches the result per design path for server lifetime.
    """
    key = str(design_path)
    if key in _base_mesh_cache:
        return _base_mesh_cache[key]

    model = rhino3dm.File3dm.Read(key)
    if model is None:
        raise PipelineError(f"Failed to read design file for base mesh")

    # Build layer index -> name map; identify zone FACE layers to skip
    layer_names = {}
    zone_face_layers = set()
    for i in range(len(model.Layers)):
        name = model.Layers[i].Name
        layer_names[model.Layers[i].Index] = name
        if re.match(r"FP_ZONE_\d+_FACE", name):
            zone_face_layers.add(model.Layers[i].Index)

    # Build instance definition cache (id -> meshed verts/normals/tris)
    idef_meshes = {}
    for idef in model.InstanceDefinitions:
        obj_ids = idef.GetObjectIds()
        all_v, all_n, all_t = [], [], []
        offset = 0
        for oid in obj_ids:
            for obj in model.Objects:
                if str(obj.Attributes.Id) == str(oid):
                    geom = obj.Geometry
                    if isinstance(geom, rhino3dm.Brep):
                        v, n, t = _mesh_brep(geom)
                        if len(v) > 0:
                            all_v.append(v)
                            all_n.append(n)
                            all_t.append(t + offset)
                            offset += len(v)
                    break
        if all_v:
            idef_meshes[str(idef.Id)] = (np.vstack(all_v), np.vstack(all_n), np.vstack(all_t))
        else:
            idef_meshes[str(idef.Id)] = (np.empty((0, 3)), np.empty((0, 3)), np.empty((0, 3), dtype=int))

    # Mesh all objects
    all_verts = []
    all_norms = []
    all_tris = []
    total_offset = 0

    for obj in model.Objects:
        layer_idx = obj.Attributes.LayerIndex
        # Skip zone FACE geometry (replaced by displaced versions)
        if layer_idx in zone_face_layers:
            continue

        geom = obj.Geometry

        if isinstance(geom, rhino3dm.Brep):
            v, n, t = _mesh_brep(geom)
            if len(v) > 0:
                all_verts.append(v)
                all_norms.append(n)
                all_tris.append(t + total_offset)
                total_offset += len(v)

        elif isinstance(geom, rhino3dm.Mesh) and len(geom.Vertices) > 1:
            # Direct mesh object
            verts = np.array([[geom.Vertices[i].X, geom.Vertices[i].Y, geom.Vertices[i].Z]
                              for i in range(len(geom.Vertices))])
            tris = []
            for fi in range(len(geom.Faces)):
                f = geom.Faces[fi]
                tris.append([f[0], f[1], f[2]])
                if len(f) > 3 and f[3] != f[2]:
                    tris.append([f[0], f[2], f[3]])
            if tris:
                tris_arr = np.array(tris, dtype=int)
                norms = _compute_mesh_normals(verts, tris_arr)
                all_verts.append(verts)
                all_norms.append(norms)
                all_tris.append(tris_arr + total_offset)
                total_offset += len(verts)

        elif isinstance(geom, rhino3dm.InstanceReference):
            idef_id = str(geom.ParentIdefId)
            if idef_id in idef_meshes:
                def_v, def_n, def_t = idef_meshes[idef_id]
                if len(def_v) > 0:
                    transformed_v = _apply_transform(def_v, geom.Xform)
                    transformed_n = _apply_normal_transform(def_n, geom.Xform)
                    all_verts.append(transformed_v)
                    all_norms.append(transformed_n)
                    all_tris.append(def_t + total_offset)
                    total_offset += len(transformed_v)

    if not all_verts:
        mesh_bytes = struct.pack("<II", 0, 0)
    else:
        merged_v = np.vstack(all_verts)
        merged_n = np.vstack(all_norms)
        merged_t = np.vstack(all_tris)
        mesh_bytes = _build_mesh_binary(merged_v, merged_n, merged_t)

    _base_mesh_cache[key] = mesh_bytes
    return mesh_bytes


def generate_preview_stl(
    design_path,
    fingerprint_file,
    zones,
    mode="emboss",
    depth=0.3,
    resolution=200,
    unified=False,
):
    """Run the pipeline and return STL bytes per zone.

    Args:
        design_path: Path to the .3dm design file
        fingerprint_file: Uploaded fingerprint image (file-like or path)
        zones: List of zone numbers to process
        mode: "emboss" or "engrave"
        depth: Max displacement in mm, or dict mapping zone_num -> depth for per-zone depth
        resolution: Grid resolution
        unified: If True, map one fingerprint across all zones

    Returns:
        Dict mapping zone number -> STL file bytes
        Example: {1: b"...", 2: b"..."}
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        # Save uploaded fingerprint to temp file
        fp_tmp_path = tmp_dir / "fingerprint.png"
        if hasattr(fingerprint_file, "read"):
            fp_data = fingerprint_file.read()
            fp_tmp_path.write_bytes(fp_data)
            if hasattr(fingerprint_file, "seek"):
                fingerprint_file.seek(0)
        else:
            # It's a path
            import shutil
            shutil.copy2(str(fingerprint_file), str(fp_tmp_path))

        # Preprocess fingerprint
        try:
            fp_img = preprocess_fingerprint(str(fp_tmp_path))
        except Exception as e:
            raise PipelineError(f"Fingerprint preprocessing failed: {e}")

        # Read design model
        try:
            model = rhino3dm.File3dm.Read(str(design_path))
        except Exception as e:
            raise PipelineError(f"Failed to read design file: {e}")

        if model is None:
            raise PipelineError("Failed to read design file: model is None")

        # Compute unified mapping if requested
        global_cx = global_cy = global_scale = None
        if unified and len(zones) > 1:
            from fingerprint_displace import find_zone_face
            import numpy as np

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

        # Process each zone
        results = {}
        feather = settings.PIPELINE_DEFAULTS.get("feather", 10)

        # None = fingerprint fills the entire zone(s) edge-to-edge.
        # Set to e.g. 17.0 for manufacturing (constrains to physical fingerprint size).
        fp_natural_width = None

        for zone_num in zones:
            try:
                zone_depth = depth[zone_num] if isinstance(depth, dict) else depth
                display_mesh, stl_mesh, face_brep, body_brep = process_zone(
                    model, zone_num, fp_img, zone_depth, resolution, mode,
                    feather_cells=feather, do_stl=True,
                    global_cx=global_cx, global_cy=global_cy,
                    global_scale=global_scale,
                    fp_natural_width=fp_natural_width,
                )
            except SystemExit as e:
                raise PipelineError(f"Zone {zone_num} processing failed: {e}")
            except Exception as e:
                raise PipelineError(f"Zone {zone_num} processing failed: {e}")

            if stl_mesh is None:
                raise PipelineError(f"Zone {zone_num}: no STL mesh produced")

            # Export STL to temp file, read bytes
            stl_path = tmp_dir / f"zone_{zone_num}.stl"
            export_stl(stl_mesh, str(stl_path))
            results[zone_num] = stl_path.read_bytes()

        return results
