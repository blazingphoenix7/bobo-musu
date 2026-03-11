#!/usr/bin/env python3
"""
Fingerprint Displacement Pipeline — Option A
==============================================
Applies a customer fingerprint image as 3D displacement onto a marked
fingerprint zone of a jewelry .3dm file.  The designer provides each zone
as two objects: FP_ZONE_N_FACE (the top face) and FP_ZONE_N_BODY (the rest).

Usage:
    python fingerprint_displace.py input.3dm fingerprint.png \
        --zone 1 --output output/out.3dm [--depth 0.3] [--resolution 200]

Dependencies (conda env bobomusu):
    rhino3dm  numpy  pillow  scipy
"""

import argparse
import math
import os
import re
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import distance_transform_edt
import rhino3dm


# ── Exception ────────────────────────────────────────────────────────

class PipelineError(Exception):
    """Raised when the displacement pipeline encounters a recoverable error."""
    pass


# ── Helpers ──────────────────────────────────────────────────────────

def _find_layer_index(model, layer_name):
    """Return layer index for a given name, or None."""
    for i in range(len(model.Layers)):
        if model.Layers[i].Name == layer_name:
            return i
    return None


def _to_brep(geo):
    """Convert a geometry object to a Brep if possible.

    Handles:
      - Brep (ObjectType 16): returned as-is
      - Surface / NurbsSurface (ObjectType 8): converted via .ToBrep()
    Returns the Brep, or None if conversion fails.
    """
    if hasattr(geo, "Faces"):
        return geo  # Already a Brep
    if hasattr(geo, "ToBrep"):
        try:
            brep = geo.ToBrep()
            if brep is not None and hasattr(brep, "Faces"):
                return brep
        except Exception:
            pass
    return None


# ── Zone Discovery (Task 1) ──────────────────────────────────────────

def _detect_zones_fp_convention(model):
    """Strategy 1: Detect zones from FP_ZONE_N_FACE layer naming convention."""
    zones = []
    for i in range(len(model.Layers)):
        m = re.match(r"FP_ZONE_(\d+)_FACE", model.Layers[i].Name)
        if m:
            zones.append(int(m.group(1)))
    return sorted(zones)


def _detect_zones_textdot(model):
    """Strategy 2: Detect zones from TextDot labels.

    Matches patterns like:
      - "Zone 1", "Zone 2" (simple labels)
      - "FP_ZONE_1_FACE", "FP_ZONE_2_BODY" (convention labels as TextDots)
    """
    zones = []
    for obj in model.Objects:
        geo = obj.Geometry
        if isinstance(geo, rhino3dm.TextDot):
            text = geo.Text if hasattr(geo, "Text") else ""
            # Try "FP_ZONE_N_..." pattern first
            m = re.match(r"FP_ZONE_(\d+)", text)
            if m:
                zones.append(int(m.group(1)))
                continue
            # Try "Zone N" pattern
            m = re.match(r"(?i)zone\s*(\d+)", text)
            if m:
                zones.append(int(m.group(1)))
    return sorted(set(zones))


def _detect_zones_fuzzy_layers(model):
    """Strategy 3: Detect zones from layers containing 'zone' or 'fp' with numbers.

    Only registers a zone if the matched layer actually contains geometry,
    to avoid false positives from empty annotation layers.
    """
    zones = set()
    for i in range(len(model.Layers)):
        name = model.Layers[i].Name.lower()
        if "zone" in name or "fp" in name:
            nums = re.findall(r"\d+", model.Layers[i].Name)
            if nums:
                layer_idx = model.Layers[i].Index
                has_geo = any(
                    obj.Attributes.LayerIndex == layer_idx
                    for obj in model.Objects
                )
                if has_geo:
                    zones.add(int(nums[0]))
    return sorted(zones)


def detect_zones(model):
    """Auto-detect all zone numbers using a multi-strategy discovery system.

    Strategies (tried in order):
    1. FP_ZONE_N_FACE layer convention (primary, existing)
    2. TextDot labels ("Zone 1", "Zone 2", etc.)
    3. Layer names containing 'zone' or 'fp' with numbers (fuzzy fallback)

    Returns sorted list of zone numbers.
    """
    # Strategy 1: FP_ZONE convention (primary path)
    zones = _detect_zones_fp_convention(model)
    if zones:
        return zones

    # Strategy 2: TextDot labels
    zones = _detect_zones_textdot(model)
    if zones:
        return zones

    # Strategy 3: Fuzzy layer name matching
    zones = _detect_zones_fuzzy_layers(model)
    if zones:
        return zones

    return []


# ── Zone Geometry Finders (Task 2) ───────────────────────────────────

def _find_zone_geo_on_layer(model, layer_name):
    """Find the first Brep-compatible geometry on a named layer.

    Tries both Brep (ObjectType 16) and Surface (ObjectType 8) objects,
    converting Surface -> Brep via _to_brep().

    Returns (obj_idx, obj, brep) or None.
    """
    layer_idx = _find_layer_index(model, layer_name)
    if layer_idx is None:
        return None
    for obj_idx, obj in enumerate(model.Objects):
        if obj.Attributes.LayerIndex == layer_idx:
            geo = obj.Geometry
            brep = _to_brep(geo)
            if brep is not None:
                return obj_idx, obj, brep
    return None


def _find_zone_geo_by_textdot(model, zone_num, role):
    """Find zone geometry near a TextDot labeled for this zone.

    Matches TextDots with labels like:
      - "FP_ZONE_N_FACE" / "FP_ZONE_N_BODY" (exact role match preferred)
      - "Zone N" (generic)

    role: 'FACE' or 'BODY' — used to pick the closest object with the
    appropriate characteristics (FACE = top surface, BODY = thicker solid).

    Returns (obj_idx, obj, brep) or None.
    """
    # Find the TextDot for this zone + role
    dot_point = None
    for obj in model.Objects:
        geo = obj.Geometry
        if isinstance(geo, rhino3dm.TextDot):
            text = geo.Text if hasattr(geo, "Text") else ""
            # Prefer exact "FP_ZONE_N_FACE" or "FP_ZONE_N_BODY" match
            m = re.match(r"FP_ZONE_(\d+)_(\w+)", text)
            if m and int(m.group(1)) == zone_num and m.group(2).upper() == role:
                pt = geo.Point
                dot_point = (pt.X, pt.Y, pt.Z)
                break
    # Fallback: generic "Zone N" label
    if dot_point is None:
        for obj in model.Objects:
            geo = obj.Geometry
            if isinstance(geo, rhino3dm.TextDot):
                text = geo.Text if hasattr(geo, "Text") else ""
                m = re.match(r"(?i)zone\s*(\d+)", text)
                if m and int(m.group(1)) == zone_num:
                    pt = geo.Point
                    dot_point = (pt.X, pt.Y, pt.Z)
                    break

    if dot_point is None:
        return None

    # Collect all Brep-compatible objects near the dot
    candidates = []
    for obj_idx, obj in enumerate(model.Objects):
        geo = obj.Geometry
        if isinstance(geo, rhino3dm.TextDot):
            continue
        brep = _to_brep(geo)
        if brep is None:
            continue
        bb = brep.GetBoundingBox()
        center = ((bb.Min.X + bb.Max.X) / 2,
                  (bb.Min.Y + bb.Max.Y) / 2,
                  (bb.Min.Z + bb.Max.Z) / 2)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(dot_point, center)))
        thickness = abs(bb.Max.Z - bb.Min.Z)
        candidates.append((dist, thickness, obj_idx, obj, brep))

    if not candidates:
        return None

    # Sort by distance to the TextDot
    candidates.sort(key=lambda c: c[0])

    if role == "FACE":
        # FACE: prefer the thinnest (flattest) geometry among nearby objects
        nearby = candidates[:min(6, len(candidates))]
        nearby.sort(key=lambda c: c[1])  # thinnest first
        return nearby[0][2], nearby[0][3], nearby[0][4]
    else:  # BODY
        # BODY: prefer the thickest geometry among nearby objects
        nearby = candidates[:min(6, len(candidates))]
        nearby.sort(key=lambda c: -c[1])  # thickest first
        return nearby[0][2], nearby[0][3], nearby[0][4]


def find_zone_face(model, zone_num):
    """Return (object_index, object, brep) for the FACE of a zone.

    Tries in order:
    1. FP_ZONE_N_FACE layer convention
    2. TextDot-based geometry association
    3. Fuzzy layer name matching

    Raises PipelineError if not found.
    """
    # Strategy 1: FP_ZONE convention
    result = _find_zone_geo_on_layer(model, f"FP_ZONE_{zone_num}_FACE")
    if result is not None:
        return result

    # Strategy 2: TextDot association
    result = _find_zone_geo_by_textdot(model, zone_num, "FACE")
    if result is not None:
        return result

    # Strategy 3: Fuzzy layer names
    for i in range(len(model.Layers)):
        name = model.Layers[i].Name
        name_lower = name.lower()
        if ("zone" in name_lower or "fp" in name_lower) and "face" in name_lower:
            nums = re.findall(r"\d+", name)
            if nums and int(nums[0]) == zone_num:
                res = _find_zone_geo_on_layer(model, name)
                if res is not None:
                    return res

    available = [model.Layers[i].Name for i in range(len(model.Layers))]
    raise PipelineError(
        f"Zone {zone_num} FACE not found. "
        f"Tried FP_ZONE_{zone_num}_FACE layer, TextDot labels, and fuzzy layer matching. "
        f"Available layers: {available}"
    )


def find_zone_body(model, zone_num):
    """Return (object_index, object, brep) for the BODY of a zone.

    Tries in order:
    1. FP_ZONE_N_BODY layer convention
    2. TextDot-based geometry association
    3. Fuzzy layer name matching

    Raises PipelineError if not found.
    """
    # Strategy 1: FP_ZONE convention
    result = _find_zone_geo_on_layer(model, f"FP_ZONE_{zone_num}_BODY")
    if result is not None:
        return result

    # Strategy 2: TextDot association
    result = _find_zone_geo_by_textdot(model, zone_num, "BODY")
    if result is not None:
        return result

    # Strategy 3: Fuzzy layer names
    for i in range(len(model.Layers)):
        name = model.Layers[i].Name
        name_lower = name.lower()
        if ("zone" in name_lower or "fp" in name_lower) and "body" in name_lower:
            nums = re.findall(r"\d+", name)
            if nums and int(nums[0]) == zone_num:
                res = _find_zone_geo_on_layer(model, name)
                if res is not None:
                    return res

    available = [model.Layers[i].Name for i in range(len(model.Layers))]
    raise PipelineError(
        f"Zone {zone_num} BODY not found. "
        f"Tried FP_ZONE_{zone_num}_BODY layer, TextDot labels, and fuzzy layer matching. "
        f"Available layers: {available}"
    )


def is_face_untrimmed(face_brep):
    """Detect if a FACE Brep is untrimmed (full surface, not zone-trimmed).

    An untrimmed face has edges that match the full underlying surface domain,
    meaning the FACE edges are NOT a useful trim boundary.

    Uses two checks:
    1. Edge count: an untrimmed rectangular surface domain has exactly 4 edges.
       Trimmed surfaces have different edge counts (P246 has 2, PDG040 has 3).
    2. BB ratio: face bounding box must closely match surface bounding box.

    Both must be satisfied to avoid false positives on curved trimmed surfaces
    where the face happens to cover most of the underlying surface.
    """
    if len(face_brep.Faces) == 0:
        return False

    # Check 1: Edge count. Untrimmed = exactly 4 edges (UV domain boundaries).
    # Trimmed surfaces have != 4 edges (P246 teardrop has 2, PDG040 slices have 3).
    n_edges = len(face_brep.Edges)
    if n_edges != 4 and n_edges != 0:
        return False

    face = face_brep.Faces[0]
    srf = face.UnderlyingSurface()

    # Check 2: BB ratio. Sample a 5x5 UV grid to estimate surface BB.
    du, dv = srf.Domain(0), srf.Domain(1)
    srf_pts = []
    n_samples = 5
    for ui in range(n_samples):
        u = du.T0 + (du.T1 - du.T0) * ui / (n_samples - 1)
        for vi in range(n_samples):
            v = dv.T0 + (dv.T1 - dv.T0) * vi / (n_samples - 1)
            p = srf.PointAt(u, v)
            srf_pts.append((p.X, p.Y, p.Z))

    srf_min = [min(p[i] for p in srf_pts) for i in range(3)]
    srf_max = [max(p[i] for p in srf_pts) for i in range(3)]

    face_bb = face_brep.GetBoundingBox()
    face_min = [face_bb.Min.X, face_bb.Min.Y, face_bb.Min.Z]
    face_max = [face_bb.Max.X, face_bb.Max.Y, face_bb.Max.Z]

    for axis in range(3):
        srf_extent = srf_max[axis] - srf_min[axis]
        face_extent = face_max[axis] - face_min[axis]
        if srf_extent > 0.001:
            ratio = face_extent / srf_extent
            if ratio < 0.95:
                return False

    return True


def _extract_boundary_from_body(body_brep, n_samples=161):
    """Extract the top-Z edges of a BODY Brep as an XY boundary.

    Used when the FACE is untrimmed (dome surface) and its edges don't
    represent the actual trim boundary. The BODY's top-Z edges define
    the real zone outline.
    """
    body_bb = body_brep.GetBoundingBox()
    top_z = body_bb.Max.Z
    z_tol = abs(body_bb.Max.Z - body_bb.Min.Z) * 0.05
    if z_tol < 0.01:
        z_tol = 0.01

    boundary = []
    for ei in range(len(body_brep.Edges)):
        edge = body_brep.Edges[ei]
        t0, t1 = edge.Domain.T0, edge.Domain.T1
        # Check if edge midpoint is near the top Z
        mid_t = (t0 + t1) / 2
        mid_p = edge.PointAt(mid_t)
        if abs(mid_p.Z - top_z) > z_tol:
            continue
        # Sample this edge (projected to XY)
        for ti in range(n_samples):
            t = t0 + (t1 - t0) * ti / (n_samples - 1)
            p = edge.PointAt(t)
            if abs(p.Z - top_z) <= z_tol:
                boundary.append((p.X, p.Y))

    if not boundary:
        # Fallback to body bounding box
        return [
            (body_bb.Min.X, body_bb.Min.Y),
            (body_bb.Max.X, body_bb.Min.Y),
            (body_bb.Max.X, body_bb.Max.Y),
            (body_bb.Min.X, body_bb.Max.Y),
        ]

    # Order by angle around centroid
    bcx = sum(p[0] for p in boundary) / len(boundary)
    bcy = sum(p[1] for p in boundary) / len(boundary)
    boundary.sort(key=lambda p: math.atan2(p[1] - bcy, p[0] - bcx))
    return boundary


def extract_trim_boundary(face_brep, n_samples=161, body_brep=None):
    """Extract the trim boundary from a FACE Brep.

    If body_brep is provided and the face is untrimmed (dome surface),
    uses the BODY's top-Z edges as the boundary instead.

    The FACE Brep's edges ARE the trim boundary — no Z-filtering needed.
    Works for both planar and curved faces.
    """
    # Task 4: If face is untrimmed and we have a BODY, use BODY boundary
    if body_brep is not None and is_face_untrimmed(face_brep):
        print("  Using BODY boundary (face is untrimmed)")
        return _extract_boundary_from_body(body_brep, n_samples)

    boundary = []
    for ei in range(len(face_brep.Edges)):
        edge = face_brep.Edges[ei]
        t0, t1 = edge.Domain.T0, edge.Domain.T1
        for ti in range(n_samples):
            t = t0 + (t1 - t0) * ti / (n_samples - 1)
            p = edge.PointAt(t)
            boundary.append((p.X, p.Y))

    if not boundary:
        bb = face_brep.GetBoundingBox()
        return [
            (bb.Min.X, bb.Min.Y),
            (bb.Max.X, bb.Min.Y),
            (bb.Max.X, bb.Max.Y),
            (bb.Min.X, bb.Max.Y),
        ]

    # Order by angle around centroid
    bcx = sum(p[0] for p in boundary) / len(boundary)
    bcy = sum(p[1] for p in boundary) / len(boundary)
    boundary.sort(key=lambda p: math.atan2(p[1] - bcy, p[0] - bcx))
    return boundary


def _pip(px, py, poly):
    """Point-in-polygon via ray casting."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


# ── Fingerprint preprocessing ────────────────────────────────────────

def preprocess_fingerprint(img_path, target_size=1024):
    """Load and preprocess a fingerprint image for displacement mapping."""
    img = Image.open(img_path).convert("L")
    arr = np.array(img, dtype=np.float64)

    mean_val = np.mean(arr)
    if mean_val > 127:
        fg_mask = arr < (mean_val - 20)
        needs_invert = True
    else:
        fg_mask = arr > (mean_val + 20)
        needs_invert = False

    rows = np.any(fg_mask, axis=1)
    cols = np.any(fg_mask, axis=0)
    if np.any(rows) and np.any(cols):
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        pad_r = max(1, int(0.05 * (rmax - rmin)))
        pad_c = max(1, int(0.05 * (cmax - cmin)))
        rmin = max(0, rmin - pad_r)
        rmax = min(arr.shape[0] - 1, rmax + pad_r)
        cmin = max(0, cmin - pad_c)
        cmax = min(arr.shape[1] - 1, cmax + pad_c)
        arr = arr[rmin:rmax + 1, cmin:cmax + 1]

    if needs_invert:
        arr = 255.0 - arr

    lo, hi = np.percentile(arr, 2), np.percentile(arr, 98)
    if hi - lo > 10:
        arr = np.clip((arr - lo) / (hi - lo) * 255.0, 0, 255)

    img_out = Image.fromarray(arr.astype(np.uint8))
    img_out = img_out.resize((target_size, target_size), Image.LANCZOS)
    img_out = img_out.filter(ImageFilter.GaussianBlur(radius=1.5))
    return img_out


# ── Main pipeline ────────────────────────────────────────────────────

def _build_displaced_mesh_single_face(face_brep, body_brep, fp_img, max_depth, grid_res, mode,
                                      feather_cells=10, watertight=False,
                                      global_cx=None, global_cy=None, global_scale=None,
                                      fp_natural_width=None, face_index=0,
                                      skip_boundary_test=False):
    """Build a displaced fingerprint mesh from a single face of a FACE Brep.

    face_brep: Brep from FP_ZONE_N_FACE
    body_brep: open polysurface Brep from FP_ZONE_N_BODY (used for thickness)
    face_index: which face of face_brep to process (default 0 for backward compat)
    fp_natural_width: If set (mm), maps fingerprint at natural physical scale.
                      None = legacy behaviour (fill zone edge-to-edge).
    skip_boundary_test: if True, include all grid points without pip test (used for
                        multi-face Breps where the UV grid is naturally bounded by
                        the face's trim and adjacent faces fill seam gaps).

    Raises PipelineError on failure.
    """
    face = face_brep.Faces[face_index]
    srf = face.UnderlyingSurface()
    du, dv = srf.Domain(0), srf.Domain(1)
    reversed_n = face.OrientationIsReversed

    # Zone thickness from BODY bounding box
    body_bb = body_brep.GetBoundingBox()
    face_bb = face_brep.GetBoundingBox()
    thickness = abs(face_bb.Max.Z - body_bb.Min.Z)
    if thickness < 0.01:
        thickness = abs(body_bb.Max.Z - body_bb.Min.Z)
    print(f"  Zone thickness: {thickness:.3f} mm")
    print(f"  Approach: thin shell on top of original zone (max {max_depth}mm thick)")

    if max_depth > thickness * 0.8:
        print(f"  WARNING: Displacement depth ({max_depth} mm) close to zone thickness "
              f"({thickness:.3f} mm). Clamping to {thickness * 0.5:.3f} mm.")
        max_depth = thickness * 0.5

    # Determine UV range for the face
    fu_min, fu_max = du.T1, du.T0
    fv_min, fv_max = dv.T1, dv.T0
    for u_p in np.linspace(du.T0, du.T1, 80):
        for v_p in np.linspace(dv.T0, dv.T1, 80):
            p = srf.PointAt(u_p, v_p)
            if (face_bb.Min.X - 0.2 <= p.X <= face_bb.Max.X + 0.2 and
                    face_bb.Min.Y - 0.2 <= p.Y <= face_bb.Max.Y + 0.2):
                fu_min = min(fu_min, u_p)
                fu_max = max(fu_max, u_p)
                fv_min = min(fv_min, v_p)
                fv_max = max(fv_max, v_p)

    print(f"  UV range: U=[{fu_min:.4f}, {fu_max:.4f}], V=[{fv_min:.4f}, {fv_max:.4f}]")

    # Trim boundary from FACE edges (Task 4: pass body_brep for untrimmed detection)
    if not skip_boundary_test:
        boundary = extract_trim_boundary(face_brep, body_brep=body_brep)
        print(f"  Trim boundary: {len(boundary)} points")
    else:
        boundary = None
        print(f"  Boundary test: SKIPPED (multi-face mode)")

    # Fingerprint as float [0,1]
    fp = np.array(fp_img.convert("L"), dtype=np.float64) / 255.0
    fp_h, fp_w = fp.shape

    # Sample grid
    u_vals = np.linspace(fu_min, fu_max, grid_res)
    v_vals = np.linspace(fv_min, fv_max, grid_res)

    print(f"  Evaluating {grid_res}x{grid_res} grid...")
    grid_pts = np.zeros((grid_res, grid_res, 3))
    grid_nrm = np.zeros((grid_res, grid_res, 3))
    grid_in = np.zeros((grid_res, grid_res), dtype=bool)

    for i, u in enumerate(u_vals):
        for j, v in enumerate(v_vals):
            pt = srf.PointAt(u, v)
            nm = srf.NormalAt(u, v)
            grid_pts[i, j] = [pt.X, pt.Y, pt.Z]
            if reversed_n:
                grid_nrm[i, j] = [-nm.X, -nm.Y, -nm.Z]
            else:
                grid_nrm[i, j] = [nm.X, nm.Y, nm.Z]
            if skip_boundary_test:
                grid_in[i, j] = True
            else:
                grid_in[i, j] = _pip(pt.X, pt.Y, boundary)

    n_inside = int(np.sum(grid_in))
    print(f"  Inside boundary: {n_inside}/{grid_res ** 2} ({100 * n_inside / grid_res ** 2:.1f}%)")

    if n_inside == 0:
        raise PipelineError("No grid points inside the trim boundary. Check boundary extraction.")

    # Zone centroid and scale for fingerprint mapping
    inside_pts = grid_pts[grid_in]
    if global_cx is not None and global_cy is not None and global_scale is not None:
        # Unified mode: use global mapping from combined bounding box
        zone_cx = global_cx
        zone_cy = global_cy
        zone_scale = global_scale
        print(f"  Using UNIFIED mapping: cx={zone_cx:.3f}, cy={zone_cy:.3f}, scale={zone_scale:.3f}")
    else:
        zone_cx = np.mean(inside_pts[:, 0])
        zone_cy = np.mean(inside_pts[:, 1])
        zone_half_x = max(abs(inside_pts[:, 0].max() - zone_cx),
                          abs(inside_pts[:, 0].min() - zone_cx))
        zone_half_y = max(abs(inside_pts[:, 1].max() - zone_cy),
                          abs(inside_pts[:, 1].min() - zone_cy))
        zone_scale = max(zone_half_x, zone_half_y) * 1.05
        print(f"  Zone centroid: ({zone_cx:.3f}, {zone_cy:.3f})")
        print(f"  Zone half-extent: X={zone_half_x:.3f}, Y={zone_half_y:.3f}, scale={zone_scale:.3f}")

    # Natural fingerprint scaling: limit mapping to physical fingerprint size
    fp_vignette_scale = None  # None = no vignette (legacy)
    if fp_natural_width is not None:
        zone_physical_width = zone_scale * 2.0  # full zone extent in mm
        fp_half = fp_natural_width / 2.0
        if zone_scale > fp_half:
            # Zone is bigger than fingerprint — scale mapping to natural size
            fp_vignette_scale = fp_half / zone_scale  # fraction of zone covered
            print(f"  Natural FP scaling: zone={zone_physical_width:.1f}mm, "
                  f"fp={fp_natural_width:.1f}mm, coverage={fp_vignette_scale*100:.0f}%")
        else:
            print(f"  Natural FP scaling: zone ({zone_physical_width:.1f}mm) smaller "
                  f"than fingerprint ({fp_natural_width:.1f}mm), using full zone")

    # Boundary distance field (EDT)
    dist_field = distance_transform_edt(grid_in)
    max_dist = np.max(dist_field)
    print(f"  Distance field: max={max_dist:.1f} cells, feather={feather_cells} cells")

    feather = np.clip(dist_field / feather_cells, 0.0, 1.0)

    # Build vertices
    mesh = rhino3dm.Mesh()
    vertex_normals = []
    front_map = np.full((grid_res, grid_res), -1, dtype=int)
    vi = 0

    for i in range(grid_res):
        for j in range(grid_res):
            if not grid_in[i, j]:
                continue
            pt = grid_pts[i, j]
            nm = grid_nrm[i, j]

            # Sample fingerprint with bilinear interpolation
            rel_x = (pt[0] - zone_cx) / zone_scale
            rel_y = (pt[1] - zone_cy) / zone_scale

            # Natural scaling: remap to fingerprint coverage area
            if fp_vignette_scale is not None:
                fp_rel_x = rel_x / fp_vignette_scale
                fp_rel_y = rel_y / fp_vignette_scale
            else:
                fp_rel_x = rel_x
                fp_rel_y = rel_y

            fi_x = (fp_rel_x * 0.5 + 0.5) * (fp_w - 1)
            fi_y = (0.5 - fp_rel_y * 0.5) * (fp_h - 1)
            fi_x = max(0.0, min(fp_w - 1.001, fi_x))
            fi_y = max(0.0, min(fp_h - 1.001, fi_y))
            ix0 = int(fi_x)
            iy0 = int(fi_y)
            ix0 = min(ix0, fp_w - 2)
            iy0 = min(iy0, fp_h - 2)
            fx = fi_x - ix0
            fy = fi_y - iy0
            brightness = (
                fp[iy0, ix0] * (1 - fx) * (1 - fy) +
                fp[iy0, ix0 + 1] * fx * (1 - fy) +
                fp[iy0 + 1, ix0] * (1 - fx) * fy +
                fp[iy0 + 1, ix0 + 1] * fx * fy
            )

            # Vignette falloff for natural scaling
            if fp_vignette_scale is not None:
                r = math.sqrt(fp_rel_x ** 2 + fp_rel_y ** 2)
                # Smooth falloff: full strength inside 80%, fades to 0 at 100%
                if r > 1.0:
                    brightness = 0.0
                elif r > 0.8:
                    brightness *= 1.0 - (r - 0.8) / 0.2  # linear fade

            f = feather[i, j]
            if mode == "engrave":
                disp = -brightness * max_depth * f
            else:
                disp = brightness * max_depth * f

            mesh.Vertices.Add(
                pt[0] + nm[0] * disp,
                pt[1] + nm[1] * disp,
                pt[2] + nm[2] * disp,
            )
            # Vertex normals: front face should point outward from the solid.
            # In emboss: front is the displaced (outer) face -> normal = surface normal
            # In engrave: front is the displaced (inner) face -> normal = -surface normal
            if mode == "engrave":
                vertex_normals.append((-nm[0], -nm[1], -nm[2]))
            else:
                vertex_normals.append((nm[0], nm[1], nm[2]))
            front_map[i, j] = vi
            vi += 1

            if watertight:
                mesh.Vertices.Add(pt[0], pt[1], pt[2])
                # Back face: opposite of front
                if mode == "engrave":
                    vertex_normals.append((nm[0], nm[1], nm[2]))
                else:
                    vertex_normals.append((-nm[0], -nm[1], -nm[2]))
                vi += 1

    if watertight:
        print(f"  Vertices: {vi} ({vi // 2} front + {vi // 2} back)")
    else:
        print(f"  Vertices: {vi} (front face only)")

    # Triangulate
    # Determine if the default winding (f0, f1, f2) matches the surface normal.
    # The UV grid winding depends on the surface parameterization, which can be
    # right-handed or left-handed. We detect this by computing the first triangle
    # normal and comparing with the grid normal at that point.
    uv_flip = False
    # Find first valid triangle in grid to test winding
    for _ti in range(grid_res - 1):
        for _tj in range(grid_res - 1):
            corners = [(i_, j_) for i_, j_ in [(_ti, _tj), (_ti + 1, _tj), (_ti + 1, _tj + 1)]
                       if grid_in[i_, j_]]
            if len(corners) == 3:
                p0 = grid_pts[corners[0][0], corners[0][1]]
                p1 = grid_pts[corners[1][0], corners[1][1]]
                p2 = grid_pts[corners[2][0], corners[2][1]]
                e1 = p1 - p0
                e2 = p2 - p0
                tri_normal = np.cross(e1, e2)
                surf_normal = grid_nrm[corners[0][0], corners[0][1]]
                dot = np.dot(tri_normal, surf_normal)
                if dot < 0:
                    uv_flip = True
                break
        else:
            continue
        break
    # In emboss mode, front face normals should match surface normal (outward)
    # In engrave mode, front face normals should be opposite (front is inner face)
    # XOR: if UV winding is flipped, cancel out; if engrave, add flip
    flip = uv_flip ^ (mode == "engrave")
    front_dir_edges = {}
    front_tri_count = 0
    back_tri_count = 0

    def add_cell_tris(corners):
        nonlocal front_tri_count, back_tri_count
        f_ids = [front_map[c[0], c[1]] for c in corners]

        def record_front_edge(v1, v2):
            key = (min(v1, v2), max(v1, v2))
            if key not in front_dir_edges:
                front_dir_edges[key] = []
            front_dir_edges[key].append((v1, v2))

        if len(corners) >= 3:
            if flip:
                mesh.Faces.AddFace(f_ids[2], f_ids[1], f_ids[0])
            else:
                mesh.Faces.AddFace(f_ids[0], f_ids[1], f_ids[2])
            record_front_edge(f_ids[0], f_ids[1])
            record_front_edge(f_ids[1], f_ids[2])
            record_front_edge(f_ids[2], f_ids[0])
            front_tri_count += 1
            if watertight:
                b_ids = [f + 1 for f in f_ids]
                if flip:
                    mesh.Faces.AddFace(b_ids[0], b_ids[1], b_ids[2])
                else:
                    mesh.Faces.AddFace(b_ids[2], b_ids[1], b_ids[0])
                back_tri_count += 1

        if len(corners) == 4:
            if flip:
                mesh.Faces.AddFace(f_ids[3], f_ids[2], f_ids[0])
            else:
                mesh.Faces.AddFace(f_ids[0], f_ids[2], f_ids[3])
            record_front_edge(f_ids[0], f_ids[2])
            record_front_edge(f_ids[2], f_ids[3])
            record_front_edge(f_ids[3], f_ids[0])
            front_tri_count += 1
            if watertight:
                b_ids = [front_map[c[0], c[1]] + 1 for c in corners]
                if flip:
                    mesh.Faces.AddFace(b_ids[0], b_ids[2], b_ids[3])
                else:
                    mesh.Faces.AddFace(b_ids[3], b_ids[2], b_ids[0])
                back_tri_count += 1

    print("  Building triangles...")
    skipped_degen = 0
    for i in range(grid_res - 1):
        for j in range(grid_res - 1):
            ins = [grid_in[i, j], grid_in[i + 1, j],
                   grid_in[i + 1, j + 1], grid_in[i, j + 1]]
            corners_all = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            corners = [c for c, inside in zip(corners_all, ins) if inside]
            if len(corners) >= 3:
                # Skip degenerate triangles (near-zero area at trim boundaries)
                p0 = grid_pts[corners[0][0], corners[0][1]]
                p1 = grid_pts[corners[1][0], corners[1][1]]
                p2 = grid_pts[corners[2][0], corners[2][1]]
                area = 0.5 * np.linalg.norm(np.cross(p1 - p0, p2 - p0))
                if area < 1e-8:
                    skipped_degen += 1
                    continue
                add_cell_tris(corners)
    if skipped_degen:
        print(f"  Skipped {skipped_degen} degenerate triangles")

    print(f"  Front triangles: {front_tri_count}")
    print(f"  Back triangles:  {back_tri_count}")

    # Side walls (watertight mode only)
    # Share vertices with front/back faces for manifold topology.
    # This means side wall normals inherit from front/back (not ideal for
    # shading, but correct for watertight STL export).
    side_count = 0
    if watertight:
        boundary_edges = []
        for key, directed_list in front_dir_edges.items():
            if len(directed_list) == 1:
                boundary_edges.append(directed_list[0])

        for fv1, fv2 in boundary_edges:
            bv1 = fv1 + 1
            bv2 = fv2 + 1
            # Side wall quad: front edge -> back edge (shared vertices)
            if flip:
                # Engrave: front is below back, reverse winding
                mesh.Faces.AddFace(bv1, bv2, fv2, fv1)
            else:
                # Emboss: front is above back
                mesh.Faces.AddFace(fv1, fv2, bv2, bv1)
            side_count += 1

    print(f"  Side-wall quads: {side_count}")
    print(f"  Total faces:     {mesh.Faces.Count}")

    for nx, ny, nz in vertex_normals:
        mesh.Normals.Add(nx, ny, nz)

    mesh.Compact()
    return mesh


def build_displaced_mesh(face_brep, body_brep, fp_img, max_depth, grid_res, mode,
                         feather_cells=10, watertight=False,
                         global_cx=None, global_cy=None, global_scale=None,
                         fp_natural_width=None):
    """Build a displaced fingerprint mesh from the FACE Brep.

    Supports multi-face Breps (Task 3): when face_brep has more than one face,
    each face is processed independently with resolution allocated proportionally
    by face area, and meshes are combined.

    For single-face Breps, produces identical results to the original code.

    Raises PipelineError on failure.
    """
    n_faces = len(face_brep.Faces)

    if n_faces <= 1:
        # Single-face: backward-compatible path
        return _build_displaced_mesh_single_face(
            face_brep, body_brep, fp_img, max_depth, grid_res, mode,
            feather_cells=feather_cells, watertight=watertight,
            global_cx=global_cx, global_cy=global_cy, global_scale=global_scale,
            fp_natural_width=fp_natural_width, face_index=0,
        )

    # Multi-face Brep: process each face independently
    print(f"  Multi-face Brep detected: {n_faces} faces")

    # Compute face areas for proportional resolution allocation
    face_areas = []
    for fi in range(n_faces):
        face = face_brep.Faces[fi]
        sub_brep = face.DuplicateFace(False)
        bb = sub_brep.GetBoundingBox()
        # Approximate area from bounding box (good enough for proportional allocation)
        area = ((bb.Max.X - bb.Min.X) * (bb.Max.Y - bb.Min.Y) +
                (bb.Max.X - bb.Min.X) * (bb.Max.Z - bb.Min.Z) +
                (bb.Max.Y - bb.Min.Y) * (bb.Max.Z - bb.Min.Z))
        face_areas.append(max(area, 0.001))

    total_area = sum(face_areas)
    min_res = max(20, grid_res // 5)

    # Combine meshes from all faces
    combined_mesh = rhino3dm.Mesh()
    combined_normals = []
    vertex_offset = 0

    for fi in range(n_faces):
        # Allocate resolution proportionally by face area
        face_frac = face_areas[fi] / total_area
        face_res = max(min_res, int(round(grid_res * math.sqrt(face_frac))))
        print(f"\n  --- Face {fi}/{n_faces} (area fraction: {face_frac:.2f}, res: {face_res}) ---")

        # Create a sub-brep for this face
        sub_brep = face_brep.Faces[fi].DuplicateFace(False)

        try:
            sub_mesh = _build_displaced_mesh_single_face(
                sub_brep, body_brep, fp_img, max_depth, face_res, mode,
                feather_cells=feather_cells, watertight=watertight,
                global_cx=global_cx, global_cy=global_cy, global_scale=global_scale,
                fp_natural_width=fp_natural_width, face_index=0,
                skip_boundary_test=True,
            )
        except PipelineError as e:
            print(f"  Face {fi} skipped: {e}")
            continue

        # Merge sub_mesh into combined_mesh
        n_sub_verts = len(sub_mesh.Vertices)
        for vi in range(n_sub_verts):
            v = sub_mesh.Vertices[vi]
            combined_mesh.Vertices.Add(v.X, v.Y, v.Z)

        for ni in range(len(sub_mesh.Normals)):
            n = sub_mesh.Normals[ni]
            combined_normals.append((n.X, n.Y, n.Z))

        for fci in range(sub_mesh.Faces.Count):
            face_verts = sub_mesh.Faces[fci]
            if len(face_verts) == 4 and face_verts[3] != face_verts[2]:
                combined_mesh.Faces.AddFace(
                    face_verts[0] + vertex_offset,
                    face_verts[1] + vertex_offset,
                    face_verts[2] + vertex_offset,
                    face_verts[3] + vertex_offset,
                )
            else:
                combined_mesh.Faces.AddFace(
                    face_verts[0] + vertex_offset,
                    face_verts[1] + vertex_offset,
                    face_verts[2] + vertex_offset,
                )

        vertex_offset += n_sub_verts

    if combined_mesh.Faces.Count == 0:
        raise PipelineError("No faces produced any mesh in multi-face Brep processing.")

    for nx, ny, nz in combined_normals:
        combined_mesh.Normals.Add(nx, ny, nz)

    combined_mesh.Compact()
    print(f"\n  Combined multi-face mesh: {len(combined_mesh.Vertices)} verts, "
          f"{combined_mesh.Faces.Count} faces")
    return combined_mesh


# ── Synthetic fingerprint generator (for testing) ────────────────────

def generate_test_fingerprint(path, size=512):
    """Create a synthetic fingerprint image for testing."""
    img = np.zeros((size, size), dtype=np.uint8)
    cx, cy = size // 2, size // 2 + 30
    for y in range(size):
        for x in range(size):
            dx = (x - cx) / 1.0
            dy = (y - cy) / 1.3
            dist = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)
            dist += 8 * math.sin(3 * angle)
            val = math.sin(dist * 2 * math.pi / 12.0)
            img[y, x] = 255 if val > 0 else 0
    Image.fromarray(img).save(path)
    print(f"  Generated test fingerprint: {path}")
    return path


# ── STL export ───────────────────────────────────────────────────────

def export_stl(mesh, path):
    """Write a binary STL from a rhino3dm Mesh. Filters degenerate triangles."""
    import struct
    triangles = []
    skipped = 0
    for fi in range(mesh.Faces.Count):
        face = mesh.Faces[fi]
        a, b, c = face[0], face[1], face[2]
        d = face[3] if len(face) > 3 else c
        v0 = mesh.Vertices[a]
        v1 = mesh.Vertices[b]
        v2 = mesh.Vertices[c]
        e1 = [v1.X - v0.X, v1.Y - v0.Y, v1.Z - v0.Z]
        e2 = [v2.X - v0.X, v2.Y - v0.Y, v2.Z - v0.Z]
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        area2 = nx * nx + ny * ny + nz * nz
        if area2 > 1e-20:
            triangles.append((nx, ny, nz, v0, v1, v2))
        else:
            skipped += 1
        if d != c:
            v3 = mesh.Vertices[d]
            e1q = [v2.X - v0.X, v2.Y - v0.Y, v2.Z - v0.Z]
            e2q = [v3.X - v0.X, v3.Y - v0.Y, v3.Z - v0.Z]
            nx2 = e1q[1] * e2q[2] - e1q[2] * e2q[1]
            ny2 = e1q[2] * e2q[0] - e1q[0] * e2q[2]
            nz2 = e1q[0] * e2q[1] - e1q[1] * e2q[0]
            area2q = nx2 * nx2 + ny2 * ny2 + nz2 * nz2
            if area2q > 1e-20:
                triangles.append((nx2, ny2, nz2, v0, v2, v3))
            else:
                skipped += 1

    with open(path, "wb") as f:
        f.write(b"\0" * 80)
        f.write(struct.pack("<I", len(triangles)))
        for nx, ny, nz, v0, v1, v2 in triangles:
            f.write(struct.pack("<fff", nx, ny, nz))
            f.write(struct.pack("<fff", v0.X, v0.Y, v0.Z))
            f.write(struct.pack("<fff", v1.X, v1.Y, v1.Z))
            f.write(struct.pack("<fff", v2.X, v2.Y, v2.Z))
            f.write(struct.pack("<H", 0))

    if skipped:
        print(f"  STL: filtered {skipped} degenerate triangles")
    print(f"  STL exported: {path} ({len(triangles)} triangles)")


# ── CLI ──────────────────────────────────────────────────────────────

def process_zone(model, zone_num, fp_img, depth, resolution, mode, feather_cells, do_stl,
                 global_cx=None, global_cy=None, global_scale=None,
                 fp_natural_width=None):
    """Process a single zone: find FACE/BODY, build meshes.

    fp_natural_width: If set (mm), maps fingerprint at natural physical scale.
                      None = legacy behaviour (fill zone edge-to-edge).

    Returns (display_mesh, stl_mesh_or_None, face_brep, body_brep).
    """
    print(f"\n  --- Zone {zone_num} ---")

    face_idx, face_obj, face_brep = find_zone_face(model, zone_num)
    body_idx, body_obj, body_brep = find_zone_body(model, zone_num)

    face_bb = face_brep.GetBoundingBox()
    body_bb = body_brep.GetBoundingBox()
    print(f"  FACE obj index: {face_idx}, faces: {len(face_brep.Faces)}")
    print(f"  FACE BB: ({face_bb.Min.X:.3f}, {face_bb.Min.Y:.3f}, {face_bb.Min.Z:.3f}) -> "
          f"({face_bb.Max.X:.3f}, {face_bb.Max.Y:.3f}, {face_bb.Max.Z:.3f})")
    print(f"  BODY obj index: {body_idx}, faces: {len(body_brep.Faces)}")
    print(f"  BODY BB: ({body_bb.Min.X:.3f}, {body_bb.Min.Y:.3f}, {body_bb.Min.Z:.3f}) -> "
          f"({body_bb.Max.X:.3f}, {body_bb.Max.Y:.3f}, {body_bb.Max.Z:.3f})")

    face0 = face_brep.Faces[0]
    srf = face0.UnderlyingSurface()
    du, dv = srf.Domain(0), srf.Domain(1)
    u_mid = (du.T0 + du.T1) / 2
    v_mid = (dv.T0 + dv.T1) / 2
    nm = srf.NormalAt(u_mid, v_mid)
    if face0.OrientationIsReversed:
        face_normal = (-nm.X, -nm.Y, -nm.Z)
    else:
        face_normal = (nm.X, nm.Y, nm.Z)
    print(f"  FACE normal: ({face_normal[0]:.3f}, {face_normal[1]:.3f}, {face_normal[2]:.3f})")
    print(f"  Mode: {mode} (depth={depth} mm)")

    print(f"\n  Building display mesh for zone {zone_num}...")
    display_mesh = build_displaced_mesh(
        face_brep, body_brep, fp_img, depth, resolution, mode,
        feather_cells=feather_cells, watertight=False,
        global_cx=global_cx, global_cy=global_cy, global_scale=global_scale,
        fp_natural_width=fp_natural_width,
    )

    stl_mesh = None
    if do_stl:
        print(f"\n  Building watertight mesh for zone {zone_num}...")
        stl_mesh = build_displaced_mesh(
            face_brep, body_brep, fp_img, depth, resolution, mode,
            feather_cells=feather_cells, watertight=True,
            global_cx=global_cx, global_cy=global_cy, global_scale=global_scale,
            fp_natural_width=fp_natural_width,
        )

    return display_mesh, stl_mesh, face_brep, body_brep


def _compute_auto_depth(model, zones):
    """Compute safe displacement depth PER ZONE: 18% of each zone's thickness, clamped to 0.02-1.0mm."""
    zone_depths = {}
    zone_thicknesses = {}
    for z in zones:
        try:
            _, _, face_brep = find_zone_face(model, z)
            _, _, body_brep = find_zone_body(model, z)
            face_bb = face_brep.GetBoundingBox()
            body_bb = body_brep.GetBoundingBox()
            thickness = abs(face_bb.Max.Z - body_bb.Min.Z)
            if thickness < 0.01:
                thickness = abs(body_bb.Max.Z - body_bb.Min.Z)
            if thickness > 0:
                zone_thicknesses[z] = thickness
                depth = round(thickness * 0.18, 3)
                zone_depths[z] = max(0.02, min(depth, 1.0))
            else:
                zone_depths[z] = 0.3
        except PipelineError:
            zone_depths[z] = 0.3
    return zone_depths, zone_thicknesses


def main():
    parser = argparse.ArgumentParser(
        description="Apply a fingerprint onto a jewelry .3dm file. Auto-detects all zones and exports both .3dm and .stl.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s designs/PDG040.3dm customer_fp.png
  %(prog)s designs/PDG040.3dm customer_fp.png --unified --depth 0.25
  %(prog)s designs/PDG040.3dm customer_fp.png --fp-width 17.0
  %(prog)s designs/PDG040.3dm customer_fp.png --output output/custom_name.3dm
        """,
    )
    parser.add_argument("input_3dm", help="Input .3dm file from designer")
    parser.add_argument("fingerprint", help="Fingerprint grayscale image (PNG/JPG)")
    parser.add_argument("--unified", action="store_true",
                        help="Map ONE fingerprint across entire pendant instead of per-zone")
    parser.add_argument("--output", help="Output .3dm path (default: output/<design>_cast.3dm)")
    parser.add_argument("--depth", type=float, default=None,
                        help="Max displacement in mm (default: auto-computed from zone thickness)")
    parser.add_argument("--resolution", type=int, default=250, help="Grid resolution (default: 250)")
    parser.add_argument("--fp-width", type=float, default=None,
                        help="Natural fingerprint width in mm (default: fill zone edge-to-edge)")
    args = parser.parse_args()

    # ── Validate inputs ──
    input_path = os.path.abspath(args.input_3dm)
    if not os.path.isfile(input_path):
        sys.exit(f"ERROR: Input file not found: {input_path}")

    fp_path = os.path.abspath(args.fingerprint)
    if not os.path.isfile(fp_path):
        sys.exit(f"ERROR: Fingerprint image not found: {fp_path}")

    # Validate image
    try:
        test_img = Image.open(fp_path)
        test_img.verify()
    except Exception:
        sys.exit(f"ERROR: Invalid image file: {fp_path}")

    if args.depth is not None and not (0.01 <= args.depth <= 2.0):
        sys.exit(f"ERROR: Depth must be between 0.01 and 2.0 mm, got {args.depth}")

    if not (50 <= args.resolution <= 500):
        sys.exit(f"ERROR: Resolution must be between 50 and 500, got {args.resolution}")

    if args.fp_width is not None and not (5.0 <= args.fp_width <= 30.0):
        sys.exit(f"ERROR: Fingerprint width must be between 5.0 and 30.0 mm, got {args.fp_width}")

    # ── Resolve paths ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(input_path))[0]

    if args.output:
        output_path = os.path.abspath(args.output)
        if not output_path.lower().endswith(".3dm"):
            output_path += ".3dm"
    elif args.unified:
        output_path = os.path.join(output_dir, f"{base_name}_unified_cast.3dm")
    else:
        output_path = os.path.join(output_dir, f"{base_name}_cast.3dm")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # ── Fingerprint image ──
    print(f"  Preprocessing fingerprint: {fp_path}")
    fp_img = preprocess_fingerprint(fp_path)
    debug_path = os.path.join(output_dir, "fingerprint_preprocessed.png")
    fp_img.save(debug_path)
    print(f"  Saved preprocessed: {debug_path}")

    print(f"  Fingerprint image: {fp_img.size[0]}x{fp_img.size[1]}")

    # ── Step 1: Read model ──
    print("\n" + "=" * 60)
    print("STEP 1: Read model")
    print("=" * 60)
    model = rhino3dm.File3dm.Read(input_path)
    print(f"  File: {input_path}")
    print(f"  Objects: {len(model.Objects)}")
    print(f"  Layers: {len(model.Layers)}")

    # ── Auto-detect all zones ──
    zones_to_process = detect_zones(model)
    if not zones_to_process:
        sys.exit("ERROR: No zones found in the model (tried FP_ZONE layers, TextDots, and fuzzy matching).")
    print(f"\n  Auto-detected {len(zones_to_process)} zone(s): {zones_to_process}")

    # ── Auto-compute depth if not specified ──
    if args.depth is not None:
        # User override: same depth for all zones
        depth_map = {z: args.depth for z in zones_to_process}
        print(f"\n  Depth: {args.depth} mm (user-specified, all zones)")
    else:
        depth_map, zone_thicknesses = _compute_auto_depth(model, zones_to_process)
        if zone_thicknesses:
            print(f"\n  Zone thicknesses: {[round(zone_thicknesses.get(z, 0), 3) for z in zones_to_process]} mm")
            for z in zones_to_process:
                t = zone_thicknesses.get(z)
                d = depth_map.get(z, 0.3)
                if t:
                    print(f"  Auto-depth zone {z}: {d} mm (18% of thickness {round(t, 3)} mm)")
                else:
                    print(f"  Auto-depth zone {z}: {d} mm (default — could not measure)")
        else:
            print(f"\n  Auto-depth: 0.3 mm (default — could not measure zone thicknesses)")

    if args.fp_width:
        print(f"  Fingerprint width: {args.fp_width} mm (natural scale)")
    else:
        print(f"  Fingerprint width: auto (fill zone edge-to-edge)")

    # ── Unified mode: compute global bounding box from all FACE surfaces ──
    global_cx = global_cy = global_scale = None
    if args.unified:
        print("\n" + "=" * 60)
        print("UNIFIED MODE: Computing global fingerprint mapping")
        print("=" * 60)
        combined_min_x = float("inf")
        combined_max_x = float("-inf")
        combined_min_y = float("inf")
        combined_max_y = float("-inf")
        for z in zones_to_process:
            _, _, face_brep = find_zone_face(model, z)
            bb = face_brep.GetBoundingBox()
            combined_min_x = min(combined_min_x, bb.Min.X)
            combined_max_x = max(combined_max_x, bb.Max.X)
            combined_min_y = min(combined_min_y, bb.Min.Y)
            combined_max_y = max(combined_max_y, bb.Max.Y)
            print(f"  Zone {z} FACE BB: X=[{bb.Min.X:.3f}, {bb.Max.X:.3f}], Y=[{bb.Min.Y:.3f}, {bb.Max.Y:.3f}]")

        global_cx = (combined_min_x + combined_max_x) / 2
        global_cy = (combined_min_y + combined_max_y) / 2
        global_half_x = (combined_max_x - combined_min_x) / 2
        global_half_y = (combined_max_y - combined_min_y) / 2
        global_scale = max(global_half_x, global_half_y) * 1.05
        print(f"  Combined BB: X=[{combined_min_x:.3f}, {combined_max_x:.3f}], "
              f"Y=[{combined_min_y:.3f}, {combined_max_y:.3f}]")
        print(f"  Global centroid: ({global_cx:.3f}, {global_cy:.3f})")
        print(f"  Global scale: {global_scale:.3f} "
              f"(half_x={global_half_x:.3f}, half_y={global_half_y:.3f})")

    # ── Step 2+3: Process each zone ──
    feather = 10
    zone_results = {}
    failed_zones = []
    for zone_num in zones_to_process:
        print("\n" + "=" * 60)
        print(f"PROCESSING ZONE {zone_num}")
        print("=" * 60)
        try:
            zone_depth = depth_map.get(zone_num, 0.3)
            display_mesh, stl_mesh, face_brep, body_brep = process_zone(
                model, zone_num, fp_img, zone_depth, args.resolution, "emboss",
                feather, True,
                global_cx=global_cx, global_cy=global_cy, global_scale=global_scale,
                fp_natural_width=args.fp_width,
            )
            zone_results[zone_num] = {
                "display_mesh": display_mesh,
                "stl_mesh": stl_mesh,
                "face_brep": face_brep,
                "body_brep": body_brep,
            }
        except PipelineError as e:
            print(f"  ERROR: Zone {zone_num} failed: {e}")
            failed_zones.append(zone_num)
            continue
        except Exception as e:
            print(f"  ERROR: Zone {zone_num} failed unexpectedly: {e}")
            failed_zones.append(zone_num)
            continue

    if not zone_results:
        sys.exit("ERROR: All zones failed to process.")

    # ── Step 4: Write output ──
    print("\n" + "=" * 60)
    print("STEP 4: Write output")
    print("=" * 60)

    out_model = rhino3dm.File3dm.Read(input_path)

    for zone_num, result in zone_results.items():
        disp_layer_name = f"FP_ZONE_{zone_num}_DISPLACED"
        disp_layer = rhino3dm.Layer()
        disp_layer.Name = disp_layer_name
        disp_layer.Color = (255, 100, 0, 255)
        out_model.Layers.Add(disp_layer)
        disp_layer_idx = len(out_model.Layers) - 1

        # Save only the watertight (closed) mesh — suitable for manufacturing
        mesh_to_save = result["stl_mesh"] if result["stl_mesh"] is not None else result["display_mesh"]
        attr = rhino3dm.ObjectAttributes()
        attr.LayerIndex = disp_layer_idx
        attr.Name = f"FP_ZONE_{zone_num}_embossed"
        out_model.Objects.AddMesh(mesh_to_save, attr)

    ok = out_model.Write(output_path, 7)
    print(f"  Output: {output_path}")
    print(f"  Write OK: {ok}")

    # Always export STLs
    output_stem = os.path.splitext(output_path)[0]
    for zone_num, result in zone_results.items():
        if result["stl_mesh"] is not None:
            stl_path = f"{output_stem}_zone{zone_num}.stl"
            export_stl(result["stl_mesh"], stl_path)

    # ── Step 5: Validate ──
    print("\n" + "=" * 60)
    print("STEP 5: Validate")
    print("=" * 60)
    val = rhino3dm.File3dm.Read(output_path)
    print(f"  Objects in output: {len(val.Objects)}")

    layer_names = [val.Layers[i].Name for i in range(len(val.Layers))]

    for zone_num in zone_results:
        mesh_name = f"FP_ZONE_{zone_num}_embossed"
        for obj in val.Objects:
            if obj.Attributes.Name == mesh_name:
                geo = obj.Geometry
                print(f"  Zone {zone_num}: {len(geo.Vertices)} vertices, {geo.Faces.Count} faces")
                bb = geo.GetBoundingBox()
                print(f"    BB: ({bb.Min.X:.3f}, {bb.Min.Y:.3f}, {bb.Min.Z:.3f}) -> "
                      f"({bb.Max.X:.3f}, {bb.Max.Y:.3f}, {bb.Max.Z:.3f})")
                break

        stl_p = f"{output_stem}_zone{zone_num}.stl"
        if os.path.isfile(stl_p):
            sz = os.path.getsize(stl_p)
            print(f"  Zone {zone_num} STL: {sz} bytes")

    # ── Summary ──
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)
    print(f"  .3dm: {output_path}")
    for zone_num in zone_results:
        print(f"  .stl: {output_stem}_zone{zone_num}.stl")
    if failed_zones:
        print(f"\n  WARNING: {len(failed_zones)} zone(s) failed: {failed_zones}")


if __name__ == "__main__":
    main()
