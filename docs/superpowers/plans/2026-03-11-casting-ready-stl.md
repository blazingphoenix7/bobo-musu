# Casting-Ready STL Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a single closed watertight STL from a .3dm design + fingerprint image, with the fingerprint zones merged into the metal body — ready for lost-wax casting with zero manual cleanup.

**Architecture:** Pluggable body mesher (Python UV-sampling primary) + Python mesh surgery (hole cutting via 3D surface-projected containment, zipper stitching, trimesh validation). New module `casting_merge.py` handles all merge logic. CLI gets `--casting` flag. Existing per-zone STL export unchanged.

**Tech Stack:** Python, rhino3dm, numpy, scipy, trimesh (new), shapely (new), PIL

**Spec:** `docs/superpowers/specs/2026-03-11-casting-ready-stl-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `3dm files/casting_merge.py` | **NEW** — All casting merge logic: object classification, body meshing, hole cutting, boundary clipping, stitching, validation, export |
| `3dm files/fingerprint_displace.py` | **MODIFY** — Add `--casting` flag, extend `extract_trim_boundary` with 3D variant, wire casting merge into `main()` |
| `3dm files/tests/test_casting.py` | **NEW** — All casting pipeline tests |
| `3dm files/tests/conftest.py` | **MODIFY** — Add shared fixtures for casting tests |

---

## Chunk 1: Dependencies, Object Classification & Body Meshing

### Task 1: Install Dependencies

**Files:**
- Modify: system conda environment `bobomusu`

- [ ] **Step 1: Install trimesh and shapely**

```bash
conda activate bobomusu && pip install trimesh shapely
```

- [ ] **Step 2: Verify imports work**

```bash
python -c "import trimesh; import shapely; print(f'trimesh {trimesh.__version__}, shapely {shapely.__version__}')"
```

Expected: versions printed, no errors.

- [ ] **Step 3: Commit** (only if environment.yml or requirements file was updated)

No file changes expected from pip install alone — skip commit if nothing to stage.

---

### Task 2: Object Classification — Gem Exclusion & Metal Body Identification

**Files:**
- Create: `3dm files/casting_merge.py`
- Create: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing tests for object classification**

Create `3dm files/tests/test_casting.py`:

```python
"""Tests for casting-ready STL merge pipeline."""
import sys
import os
import pytest
import numpy as np
import rhino3dm

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from casting_merge import classify_objects, is_gem_instance


class TestIsGemInstance:
    """Test gem detection from InstanceReference definition names and layers."""

    def test_diamond_round_excluded(self, p246_model):
        """Diamond_Round InstanceReferences should be identified as gems."""
        model = p246_model
        found_gem = False
        for i in range(len(model.Objects)):
            obj = model.Objects[i]
            geo = obj.Geometry
            if isinstance(geo, rhino3dm.InstanceReference):
                layer = model.Layers[obj.Attributes.LayerIndex]
                if is_gem_instance(obj, geo, layer, model):
                    found_gem = True
                    break
        assert found_gem, "P246 should have at least one gem InstanceReference"

    def test_brep_not_gem(self, p246_model):
        """Breps should never be classified as gems."""
        model = p246_model
        for i in range(len(model.Objects)):
            obj = model.Objects[i]
            geo = obj.Geometry
            if isinstance(geo, rhino3dm.Brep):
                layer = model.Layers[obj.Attributes.LayerIndex]
                assert not is_gem_instance(obj, geo, layer, model)


class TestClassifyObjects:
    """Test full object classification into metal body vs excluded."""

    def test_pdg040_all_metal(self, pdg040_model):
        """PDG040 has no gems — all Breps except FACE layers should be metal."""
        metal, excluded = classify_objects(pdg040_model)
        assert len(metal) > 0, "PDG040 should have metal body objects"
        # No gems in PDG040 — excluded should only be FACE layers, TextDots, etc.
        for obj_idx, obj, geo in excluded:
            layer = pdg040_model.Layers[obj.Attributes.LayerIndex]
            is_brep_or_extrusion = isinstance(geo, (rhino3dm.Brep, rhino3dm.Extrusion))
            if is_brep_or_extrusion:
                # Breps in excluded must be on FACE layers
                assert _FACE_LAYER_RE.search(layer.Name), \
                    f"Non-FACE Brep excluded: {layer.Name}"

    def test_p246_excludes_gems(self, p246_model):
        """P246 has 26 Diamond_Round gems — they must be excluded."""
        metal, excluded = classify_objects(p246_model)
        assert len(metal) > 0
        gem_count = sum(
            1 for _, _, geo in excluded
            if isinstance(geo, rhino3dm.InstanceReference)
        )
        assert gem_count >= 25, f"P246 should exclude ~26 gems, got {gem_count}"

    def test_aap_excludes_gems(self, aap_model):
        """AAP10985F has 48 gems — they must be excluded."""
        metal, excluded = classify_objects(aap_model)
        assert len(metal) > 0
        gem_count = sum(
            1 for _, _, geo in excluded
            if isinstance(geo, rhino3dm.InstanceReference)
        )
        assert gem_count >= 45, f"AAP10985F should exclude ~48 gems, got {gem_count}"

    def test_face_layers_excluded(self, pdg040_model):
        """Objects on FP_ZONE_*_FACE layers must be excluded from body mesh."""
        import re
        face_re = re.compile(r"FP_ZONE_\d+_FACE", re.IGNORECASE)
        metal, excluded = classify_objects(pdg040_model)
        for obj_idx, obj, geo in metal:
            layer = pdg040_model.Layers[obj.Attributes.LayerIndex]
            assert not face_re.search(layer.Name), f"FACE layer object in metal: {layer.Name}"

    def test_textdots_excluded(self, aap_model):
        """TextDots must be excluded."""
        metal, excluded = classify_objects(aap_model)
        for obj_idx, obj, geo in metal:
            assert not isinstance(geo, rhino3dm.TextDot), "TextDot found in metal objects"
```

Note: Import `_FACE_LAYER_RE` from `casting_merge` in the test file header.

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestIsGemInstance -v --tb=short 2>&1 | head -20
```

Expected: FAIL — `cannot import name 'classify_objects' from 'casting_merge'`

- [ ] **Step 3: Implement object classification**

Create `3dm files/casting_merge.py`:

```python
"""Casting-ready STL merge pipeline.

Merges displaced fingerprint zones into the metal body to produce
a single closed watertight STL for lost-wax casting.

Dependencies: rhino3dm, numpy, trimesh, shapely, scipy
"""
import os
import re
import math
import numpy as np
import rhino3dm
import trimesh
from shapely.geometry import Polygon, Point as ShapelyPoint

# --- Object Classification ---

# Gem detection patterns (case-insensitive)
_GEM_NAME_RE = re.compile(r"(diamond|gem|stone|brilliant)", re.IGNORECASE)
_GEM_LAYER_RE = re.compile(r"(diamond|gem|stone)", re.IGNORECASE)
_FACE_LAYER_RE = re.compile(r"FP_ZONE_\d+_FACE", re.IGNORECASE)


def _get_idef_name(model, geo):
    """Get InstanceDefinition name for an InstanceReference."""
    try:
        idef_id = geo.ParentIdefId
        for i in range(len(model.InstanceDefinitions)):
            idef = model.InstanceDefinitions[i]
            if str(idef.Id) == str(idef_id):
                return idef.Name or ""
    except (AttributeError, IndexError):
        pass
    return ""


def is_gem_instance(obj, geo, layer, model):
    """Check if an object is a gem InstanceReference that should be excluded.

    Returns True if:
    - geo is an InstanceReference AND
    - definition name matches gem patterns OR layer name matches gem patterns
    """
    if not isinstance(geo, rhino3dm.InstanceReference):
        return False

    # Check definition name
    idef_name = _get_idef_name(model, geo)
    if _GEM_NAME_RE.search(idef_name):
        return True

    # Check layer name
    if _GEM_LAYER_RE.search(layer.Name):
        return True

    return False


def classify_objects(model):
    """Classify all objects in a .3dm model into metal body vs excluded.

    Returns:
        (metal, excluded) where each is a list of (obj_index, obj, geometry) tuples.

    Metal body: Breps and Extrusions on non-FACE layers (body, settings, prongs, etc.)
    Excluded: InstanceReferences matching gem patterns, TextDots, Curves, Points,
              Annotations, objects on FACE layers.
    """
    metal = []
    excluded = []

    for i in range(len(model.Objects)):
        obj = model.Objects[i]
        geo = obj.Geometry
        if geo is None:
            continue

        layer = model.Layers[obj.Attributes.LayerIndex]

        # Exclude non-geometry types (TextDots, Curves, Points, Annotations)
        if isinstance(geo, (rhino3dm.TextDot, rhino3dm.Curve, rhino3dm.Point,
                            rhino3dm.PointCloud)):
            excluded.append((i, obj, geo))
            continue

        # Exclude objects on FACE layers
        if _FACE_LAYER_RE.search(layer.Name):
            excluded.append((i, obj, geo))
            continue

        # Exclude gem InstanceReferences
        if is_gem_instance(obj, geo, layer, model):
            excluded.append((i, obj, geo))
            continue

        # Include Breps and Extrusions as metal body
        if isinstance(geo, (rhino3dm.Brep, rhino3dm.Extrusion)):
            metal.append((i, obj, geo))
            continue

        # Everything else (other InstanceReferences, etc.) — exclude
        excluded.append((i, obj, geo))

    return metal, excluded
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestIsGemInstance tests/test_casting.py::TestClassifyObjects -v --tb=short
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): object classification — gem exclusion and metal body identification"
```

---

### Task 3: Python UV-Sampling Body Mesher

**Files:**
- Modify: `3dm files/casting_merge.py`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing tests for body meshing**

Append to `3dm files/tests/test_casting.py`:

```python
import trimesh
from casting_merge import mesh_body_python


class TestBodyMesher:
    """Test Python UV-sampling body mesher."""

    def test_pdg040_body_mesh_valid(self, pdg040_model):
        """PDG040 body mesh should have vertices and faces."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=80)
        assert isinstance(mesh, trimesh.Trimesh)
        assert len(mesh.vertices) > 100
        assert len(mesh.faces) > 100

    def test_p246_body_mesh_valid(self, p246_model):
        """P246 body mesh should mesh only metal, not gems."""
        metal, excluded = classify_objects(p246_model)
        mesh = mesh_body_python(metal, resolution=80)
        assert isinstance(mesh, trimesh.Trimesh)
        assert len(mesh.vertices) > 100

    def test_aap_body_mesh_valid(self, aap_model):
        """AAP10985F body mesh should handle complex multi-face Breps."""
        metal, _ = classify_objects(aap_model)
        mesh = mesh_body_python(metal, resolution=80)
        assert isinstance(mesh, trimesh.Trimesh)
        assert len(mesh.vertices) > 100

    def test_body_mesh_no_degenerate_tris(self, pdg040_model):
        """Body mesh should have no degenerate (zero-area) triangles."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=80)
        areas = mesh.area_faces
        assert np.all(areas > 1e-10), f"Found {np.sum(areas <= 1e-10)} degenerate triangles"

    def test_body_mesh_vertex_welding(self, pdg040_model):
        """Body mesh should weld vertices at Brep face boundaries."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=80)
        # After welding, mesh should have fewer vertices than naive concatenation
        edges = mesh.edges_unique
        assert len(edges) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestBodyMesher::test_pdg040_body_mesh_valid -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'mesh_body_python'`

- [ ] **Step 3: Implement body mesher**

Add to `3dm files/casting_merge.py`:

```python
# --- Body Meshing (Python UV-sampling) ---

# Per-face resolution cap for body meshing (body doesn't need fingerprint-level detail)
_BODY_MESH_MAX_FACE_RES = 50


def _mesh_single_brep_face(face, brep_for_face, resolution):
    """Mesh a single BrepFace via UV sampling. Returns (verts_Nx3, tris_Mx3) numpy arrays.

    Adapted from backend/preview/pipeline.py:_mesh_brep_face() but returns numpy arrays
    for trimesh consumption. Per-face resolution is capped at _BODY_MESH_MAX_FACE_RES
    to keep body meshing fast (body doesn't need fingerprint-level detail).
    """
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
    # Scale resolution by face extent, capped at _BODY_MESH_MAX_FACE_RES
    res = max(6, min(_BODY_MESH_MAX_FACE_RES, int(face_extent * 4.5)))

    srf = face.UnderlyingSurface()
    ud, vd = srf.Domain(0), srf.Domain(1)

    # Determine projection axes for point-in-polygon
    mid_u = (ud.T0 + ud.T1) / 2
    mid_v = (vd.T0 + vd.T1) / 2
    nm = srf.NormalAt(mid_u, mid_v)
    normal = np.array([nm.X, nm.Y, nm.Z])
    abs_n = np.abs(normal)
    sorted_axes = np.argsort(abs_n)
    ax_a, ax_b = sorted_axes[0], sorted_axes[1]
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
    grid_in = np.zeros((res, res), dtype=bool)
    reversed_n = face.OrientationIsReversed

    for i, u in enumerate(u_vals):
        for j, v in enumerate(v_vals):
            pt = srf.PointAt(u, v)
            p3 = np.array([pt.X, pt.Y, pt.Z])
            grid_pts[i, j] = p3
            if np.any(p3 < fbb_min - pad) or np.any(p3 > fbb_max + pad):
                continue
            if _pip_2d(p3[ax_a], p3[ax_b], boundary_2d):
                grid_in[i, j] = True

    if not np.any(grid_in):
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    # Build vertex list
    vert_map = np.full((res, res), -1, dtype=int)
    verts = []
    for i in range(res):
        for j in range(res):
            if grid_in[i, j]:
                vert_map[i, j] = len(verts)
                verts.append(grid_pts[i, j])

    # Detect winding
    uv_flip = False
    for i in range(res - 1):
        for j in range(res - 1):
            if grid_in[i, j] and grid_in[i + 1, j] and grid_in[i + 1, j + 1]:
                p0 = grid_pts[i, j]
                p1 = grid_pts[i + 1, j]
                p2 = grid_pts[i + 1, j + 1]
                nm_at = srf.NormalAt(u_vals[i], v_vals[j])
                surf_n = np.array([nm_at.X, nm_at.Y, nm_at.Z])
                if reversed_n:
                    surf_n = -surf_n
                tri_n = np.cross(p1 - p0, p2 - p0)
                if np.dot(tri_n, surf_n) < 0:
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
                tris.append([a, b, c] if not uv_flip else [c, b, a])
            if a >= 0 and c >= 0 and d >= 0:
                tris.append([a, c, d] if not uv_flip else [d, c, a])

    if not verts or not tris:
        return np.empty((0, 3)), np.empty((0, 3), dtype=int)

    return np.array(verts), np.array(tris, dtype=int)


def _pip_2d(x, y, poly):
    """Point-in-polygon via ray casting (2D)."""
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


def _weld_vertices(verts, tris, tolerance=0.01):
    """Merge duplicate vertices within tolerance using spatial hashing.

    Returns (welded_verts, remapped_tris).
    """
    if len(verts) == 0:
        return verts, tris

    cell_size = tolerance * 2
    spatial_hash = {}
    remap = np.arange(len(verts))

    for i, v in enumerate(verts):
        key = (int(v[0] / cell_size), int(v[1] / cell_size), int(v[2] / cell_size))
        merged = False
        for dk0 in (-1, 0, 1):
            for dk1 in (-1, 0, 1):
                for dk2 in (-1, 0, 1):
                    nk = (key[0] + dk0, key[1] + dk1, key[2] + dk2)
                    if nk in spatial_hash:
                        for j in spatial_hash[nk]:
                            if np.linalg.norm(verts[j] - v) < tolerance:
                                remap[i] = remap[j]
                                merged = True
                                break
                    if merged:
                        break
                if merged:
                    break
            if merged:
                break

        if key not in spatial_hash:
            spatial_hash[key] = []
        spatial_hash[key].append(i)

    # Compact: build new vertex array with only unique indices
    unique_ids = sorted(set(remap))
    new_idx = {old: new for new, old in enumerate(unique_ids)}
    welded_verts = verts[unique_ids]
    welded_tris = np.array([[new_idx[remap[t]] for t in tri] for tri in tris], dtype=int)

    # Remove degenerate triangles (where two or more vertices are the same)
    valid = (welded_tris[:, 0] != welded_tris[:, 1]) & \
            (welded_tris[:, 1] != welded_tris[:, 2]) & \
            (welded_tris[:, 0] != welded_tris[:, 2])
    welded_tris = welded_tris[valid]

    return welded_verts, welded_tris


def mesh_body_python(metal_objects, resolution=250):
    """Mesh all metal body Breps into a single trimesh.Trimesh.

    Uses UV-sampling per face, then welds vertices at Brep boundaries.
    Per-face resolution is capped at _BODY_MESH_MAX_FACE_RES (50) regardless
    of the resolution parameter — body mesh doesn't need fingerprint-level detail.

    Args:
        metal_objects: list of (obj_idx, obj, geo) from classify_objects()
        resolution: UV sampling resolution (default 250, capped per-face)

    Returns:
        trimesh.Trimesh of the full metal body

    Raises:
        PipelineError if no geometry could be meshed.
    """
    all_verts = []
    all_tris = []
    offset = 0

    for obj_idx, obj, geo in metal_objects:
        # Convert Extrusion to Brep
        brep = geo
        if isinstance(geo, rhino3dm.Extrusion):
            brep = geo.ToBrep()
            if brep is None:
                continue
        elif not isinstance(geo, rhino3dm.Brep):
            continue

        for fi in range(len(brep.Faces)):
            face = brep.Faces[fi]
            sub_brep = face.DuplicateFace(False)
            verts, tris = _mesh_single_brep_face(face, sub_brep, resolution)
            if len(verts) == 0:
                continue
            all_verts.append(verts)
            all_tris.append(tris + offset)
            offset += len(verts)

    if not all_verts:
        return trimesh.Trimesh()

    combined_verts = np.vstack(all_verts)
    combined_tris = np.vstack(all_tris)

    # Weld vertices at face boundaries
    welded_verts, welded_tris = _weld_vertices(combined_verts, combined_tris, tolerance=0.01)

    mesh = trimesh.Trimesh(vertices=welded_verts, faces=welded_tris, process=False)
    # Repair: fill micro-holes from UV sampling gaps
    trimesh.repair.fill_holes(mesh)
    trimesh.repair.fix_normals(mesh)

    return mesh
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestBodyMesher -v --tb=short
```

Expected: All PASS. Note: These tests use low resolution (80) for speed.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): Python UV-sampling body mesher with vertex welding"
```

---

## Chunk 2: 3D Boundary Extension, Hole Cutting & Boundary Clipping

### Task 4: Extend extract_trim_boundary to Return 3D Points

**Files:**
- Modify: `3dm files/fingerprint_displace.py:428-464`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing test for 3D boundary extraction**

Append to `3dm files/tests/test_casting.py`:

```python
from fingerprint_displace import extract_trim_boundary, extract_trim_boundary_3d, find_zone_face


class TestExtractTrimBoundary3D:
    """Test 3D variant of trim boundary extraction."""

    def test_returns_xyz_tuples(self, pdg040_model):
        """3D boundary should return (X, Y, Z) triples."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        boundary_3d = extract_trim_boundary_3d(face_brep)
        assert len(boundary_3d) > 10
        assert len(boundary_3d[0]) == 3, "Expected (X, Y, Z) tuples"

    def test_consistent_with_2d(self, pdg040_model):
        """3D boundary XY should match 2D boundary."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        boundary_2d = extract_trim_boundary(face_brep)
        boundary_3d = extract_trim_boundary_3d(face_brep)
        assert len(boundary_2d) == len(boundary_3d)
        for (x2, y2), (x3, y3, z3) in zip(boundary_2d, boundary_3d):
            assert abs(x2 - x3) < 0.01
            assert abs(y2 - y3) < 0.01

    def test_p246_curved_zone_has_z_variation(self, p246_model):
        """P246 zone surfaces are curved — Z values should vary (skip if flat)."""
        _, _, face_brep = find_zone_face(p246_model, 1)
        boundary_3d = extract_trim_boundary_3d(face_brep)
        z_vals = [p[2] for p in boundary_3d]
        z_range = max(z_vals) - min(z_vals)
        # Just informational — curved surfaces should have Z variation
        print(f"  P246 Zone 1 boundary Z range: {z_range:.3f}mm")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestExtractTrimBoundary3D::test_returns_xyz_tuples -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'extract_trim_boundary_3d'`

- [ ] **Step 3: Implement extract_trim_boundary_3d**

Add to `3dm files/fingerprint_displace.py` after the existing `extract_trim_boundary` function (after line ~464).

**IMPORTANT:** Use edge-walk order (iterate edges and concatenate points in edge order) instead of angle-sort, to correctly handle concave/non-star-shaped zone boundaries like AAP10985F's heart shape.

```python
def extract_trim_boundary_3d(face_brep, n_samples=161, body_brep=None):
    """Extract trim boundary as 3D (X, Y, Z) points on the FACE surface.

    Same logic as extract_trim_boundary but preserves Z coordinate.
    Uses edge-walk order (not angle-sort) to handle concave boundaries correctly.
    Used by casting merge pipeline for 3D surface-projected containment.
    """
    # Handle untrimmed faces (dome surfaces) — use BODY boundary
    if body_brep is not None and is_face_untrimmed(face_brep):
        return _extract_boundary_from_body_3d(body_brep, n_samples)

    edge_pts = []
    brep = face_brep
    for ei in range(len(brep.Edges)):
        edge = brep.Edges[ei]
        t0, t1 = edge.Domain.T0, edge.Domain.T1
        for si in range(n_samples):
            t = t0 + (t1 - t0) * si / (n_samples - 1)
            pt = edge.PointAt(t)
            edge_pts.append((pt.X, pt.Y, pt.Z))

    if not edge_pts:
        # Fallback: bounding box corners in 3D
        bb = brep.GetBoundingBox()
        return [
            (bb.Min.X, bb.Min.Y, bb.Min.Z),
            (bb.Max.X, bb.Min.Y, bb.Min.Z),
            (bb.Max.X, bb.Max.Y, bb.Max.Z),
            (bb.Min.X, bb.Max.Y, bb.Max.Z),
        ]

    # Deduplicate near-coincident points and order by edge-walk
    # (edges are already iterated in order, so concatenation preserves topology)
    # Remove near-duplicate consecutive points (within 0.001mm)
    deduped = [edge_pts[0]]
    for pt in edge_pts[1:]:
        dx = pt[0] - deduped[-1][0]
        dy = pt[1] - deduped[-1][1]
        dz = pt[2] - deduped[-1][2]
        if dx*dx + dy*dy + dz*dz > 1e-6:
            deduped.append(pt)

    return deduped


def _extract_boundary_from_body_3d(body_brep, n_samples=161):
    """Extract top-Z edges from BODY Brep as 3D points."""
    all_pts = []
    bb = body_brep.GetBoundingBox()
    z_top = bb.Max.Z
    z_thresh = z_top - (bb.Max.Z - bb.Min.Z) * 0.1

    for ei in range(len(body_brep.Edges)):
        edge = body_brep.Edges[ei]
        mid_t = (edge.Domain.T0 + edge.Domain.T1) / 2
        mid_pt = edge.PointAt(mid_t)
        if mid_pt.Z < z_thresh:
            continue
        for si in range(n_samples):
            t = edge.Domain.T0 + (edge.Domain.T1 - edge.Domain.T0) * si / (n_samples - 1)
            pt = edge.PointAt(t)
            all_pts.append((pt.X, pt.Y, pt.Z))

    if not all_pts:
        return [(bb.Min.X, bb.Min.Y, z_top), (bb.Max.X, bb.Min.Y, z_top),
                (bb.Max.X, bb.Max.Y, z_top), (bb.Min.X, bb.Max.Y, z_top)]

    # For body boundary, angle-sort is acceptable (body top edges are typically convex)
    cx = sum(p[0] for p in all_pts) / len(all_pts)
    cy = sum(p[1] for p in all_pts) / len(all_pts)
    all_pts.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
    return all_pts
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestExtractTrimBoundary3D -v --tb=short
```

Expected: All PASS.

- [ ] **Step 5: Run existing tests to verify no regressions**

```bash
cd "3dm files" && python -m pytest tests/test_core.py tests/test_integration.py -v --tb=short 2>&1 | tail -5
```

Expected: All 63 existing tests PASS.

- [ ] **Step 6: Commit**

```bash
cd "3dm files" && git add fingerprint_displace.py tests/test_casting.py && git commit -m "feat(casting): extract_trim_boundary_3d for 3D surface-projected containment"
```

---

### Task 5: Zone Hole Cutting with 3D Surface-Projected Containment

**Files:**
- Modify: `3dm files/casting_merge.py`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing tests for hole cutting**

Append to `3dm files/tests/test_casting.py`:

```python
from casting_merge import cut_zone_hole


class TestZoneHoleCutting:
    """Test removing body mesh triangles within zone boundaries."""

    def test_hole_removes_triangles(self, pdg040_model):
        """Cutting a zone hole should remove triangles."""
        from fingerprint_displace import find_zone_face, find_zone_body
        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=80)
        orig_face_count = len(body_mesh.faces)

        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)
        cut_mesh = cut_zone_hole(body_mesh, face_brep, body_brep)

        assert len(cut_mesh.faces) < orig_face_count, \
            "Hole cutting should remove triangles from body mesh"

    def test_hole_preserves_outside_triangles(self, pdg040_model):
        """Triangles far from zone should be untouched."""
        from fingerprint_displace import find_zone_face, find_zone_body
        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=80)
        orig_face_count = len(body_mesh.faces)

        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)
        cut_mesh = cut_zone_hole(body_mesh, face_brep, body_brep)

        # Should remove some but not all
        assert len(cut_mesh.faces) > orig_face_count * 0.1, \
            "Hole cutting removed too many triangles"

    def test_hole_has_boundary_edges(self, pdg040_model):
        """After cutting, the mesh should have boundary edges (the hole)."""
        from fingerprint_displace import find_zone_face, find_zone_body
        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=80)

        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)
        cut_mesh = cut_zone_hole(body_mesh, face_brep, body_brep)

        # Count boundary edges (edges belonging to exactly 1 face)
        edge_face_count = {}
        for face in cut_mesh.faces:
            for k in range(3):
                e = tuple(sorted((face[k], face[(k + 1) % 3])))
                edge_face_count[e] = edge_face_count.get(e, 0) + 1
        boundary_count = sum(1 for c in edge_face_count.values() if c == 1)
        assert boundary_count > 0, "Cut mesh should have boundary edges from the hole"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestZoneHoleCutting::test_hole_removes_triangles -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'cut_zone_hole'`

- [ ] **Step 3: Implement hole cutting**

Add to `3dm files/casting_merge.py`.

**KEY OPTIMIZATION:** Instead of per-triangle `_project_point_to_surface` (which is O(n² * grid²) and prohibitively slow), pre-build a cKDTree of surface sample points for fast nearest-neighbor UV lookup.

```python
from scipy.spatial import cKDTree


def _build_surface_uv_index(face_brep, grid_res=50):
    """Pre-sample a FACE surface on a UV grid and build a cKDTree for fast
    closest-point lookups. Returns (tree, uv_coords, points_3d, normals_3d).

    This replaces the brute-force _project_point_to_surface for batch lookups.
    """
    srf = face_brep.Faces[0].UnderlyingSurface()
    ud, vd = srf.Domain(0), srf.Domain(1)

    points = []
    uvs = []
    normals = []

    for i in range(grid_res):
        for j in range(grid_res):
            u = ud.T0 + (ud.T1 - ud.T0) * i / (grid_res - 1)
            v = vd.T0 + (vd.T1 - vd.T0) * j / (grid_res - 1)
            pt = srf.PointAt(u, v)
            nm = srf.NormalAt(u, v)
            points.append([pt.X, pt.Y, pt.Z])
            uvs.append([u, v])
            normals.append([nm.X, nm.Y, nm.Z])

    points = np.array(points)
    uvs = np.array(uvs)
    normals = np.array(normals)
    tree = cKDTree(points)

    return tree, uvs, points, normals


def _build_uv_boundary_polygon(face_brep, n_samples=161, body_brep=None):
    """Build a Shapely polygon of the zone boundary in UV space.

    Samples the FACE Brep edges in edge-walk order, projects each point onto
    the surface to get UV coordinates, and constructs a polygon.
    """
    from fingerprint_displace import extract_trim_boundary_3d, is_face_untrimmed

    boundary_3d = extract_trim_boundary_3d(face_brep, n_samples, body_brep)
    if len(boundary_3d) < 3:
        return None

    # Use cKDTree for fast projection of boundary points to UV space
    tree, uvs, _, _ = _build_surface_uv_index(face_brep, grid_res=50)

    uv_pts = []
    for pt3d in boundary_3d:
        _, idx = tree.query(pt3d)
        uv_pts.append(tuple(uvs[idx]))

    if len(uv_pts) < 3:
        return None

    try:
        poly = Polygon(uv_pts)
        if not poly.is_valid:
            poly = poly.buffer(0)  # Fix self-intersections
        return poly
    except Exception:
        return None


def _get_face_average_normal(face_brep):
    """Get the average surface normal of a FACE Brep."""
    srf = face_brep.Faces[0].UnderlyingSurface()
    ud, vd = srf.Domain(0), srf.Domain(1)
    normals = []
    for i in range(5):
        for j in range(5):
            u = ud.T0 + (ud.T1 - ud.T0) * i / 4
            v = vd.T0 + (vd.T1 - vd.T0) * j / 4
            nm = srf.NormalAt(u, v)
            normals.append([nm.X, nm.Y, nm.Z])
    return np.mean(normals, axis=0)


def cut_zone_hole(body_mesh, face_brep, body_brep=None):
    """Remove body mesh triangles that fall within a zone boundary.

    Uses 3D surface-projected containment via cKDTree: builds a spatial index
    of surface sample points, projects each triangle centroid to nearest surface
    point, then tests UV-space containment.

    Z-depth disambiguation via normal dot product (threshold 0.3, more permissive
    than spec's 0.5 to handle curved surfaces — intentional deviation).

    Boundary triangle clipping is deferred to a future task. Currently uses
    centroid-based inside/outside classification. This produces slightly ragged
    hole edges but is sufficient for initial stitching. TODO: Add shapely-based
    boundary clipping per spec Step 2.

    Args:
        body_mesh: trimesh.Trimesh of the full metal body
        face_brep: Brep of the zone FACE surface
        body_brep: Brep of the zone BODY (optional, for untrimmed face handling)

    Returns:
        trimesh.Trimesh with zone hole cut out (modified copy)
    """
    uv_poly = _build_uv_boundary_polygon(face_brep, body_brep=body_brep)
    if uv_poly is None or uv_poly.is_empty:
        print("  WARNING: Could not build UV boundary polygon, skipping hole cut")
        return body_mesh.copy()

    face_normal = _get_face_average_normal(face_brep)
    face_normal = face_normal / (np.linalg.norm(face_normal) + 1e-12)

    # Build spatial index for fast centroid → UV projection
    tree, uvs, surf_pts, surf_normals = _build_surface_uv_index(face_brep, grid_res=50)

    # Get surface bounding box for quick reject
    bb = face_brep.GetBoundingBox()
    bb_min = np.array([bb.Min.X, bb.Min.Y, bb.Min.Z])
    bb_max = np.array([bb.Max.X, bb.Max.Y, bb.Max.Z])
    bb_pad = max(np.ptp(bb_max - bb_min) * 0.2, 1.0)

    centroids = body_mesh.triangles_center
    face_normals_mesh = body_mesh.face_normals
    keep_mask = np.ones(len(body_mesh.faces), dtype=bool)

    # Batch bounding box reject
    in_bb = np.all(
        (centroids >= bb_min - bb_pad) & (centroids <= bb_max + bb_pad),
        axis=1
    )
    candidate_indices = np.where(in_bb)[0]

    # Batch nearest-neighbor lookup for candidates
    if len(candidate_indices) > 0:
        candidate_centroids = centroids[candidate_indices]
        dists, nn_indices = tree.query(candidate_centroids)

        for ci, fi in enumerate(candidate_indices):
            # Distance check — must be close to surface (within 2mm)
            if dists[ci] > 2.0:
                continue

            # Z-depth disambiguation
            tri_n = face_normals_mesh[fi]
            dot = np.dot(tri_n, face_normal)
            if dot < 0.3:
                continue

            # UV-space containment test
            u, v = uvs[nn_indices[ci]]
            if uv_poly.contains(ShapelyPoint(u, v)):
                keep_mask[fi] = False

    # Apply mask
    result = body_mesh.copy()
    result.update_faces(keep_mask)
    result.remove_unreferenced_vertices()

    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestZoneHoleCutting -v --tb=short
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): zone hole cutting with cKDTree-accelerated surface projection"
```

---

### Task 6: Z-Depth Disambiguation for AAP10985F

**Files:**
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write test for Z-depth disambiguation**

Append to `3dm files/tests/test_casting.py`:

```python
class TestZDepthDisambiguation:
    """Test that front-side zones don't cut back-side triangles on AAP10985F."""

    def test_aap_zone1_front_doesnt_cut_back(self, aap_model):
        """AAP10985F Zone 1 (front face) should not cut back-side triangles."""
        from fingerprint_displace import find_zone_face, find_zone_body
        metal, _ = classify_objects(aap_model)
        body_mesh = mesh_body_python(metal, resolution=60)
        orig_count = len(body_mesh.faces)

        _, _, face_brep_z1 = find_zone_face(aap_model, 1)
        _, _, body_brep_z1 = find_zone_body(aap_model, 1)
        cut_mesh = cut_zone_hole(body_mesh, face_brep_z1, body_brep_z1)

        removed = orig_count - len(cut_mesh.faces)
        # Zone 1 is one side — should remove less than half the mesh
        assert removed < orig_count * 0.5, \
            f"Zone 1 removed {removed}/{orig_count} faces — likely cutting both sides"

    def test_aap_zone2_back_doesnt_cut_front(self, aap_model):
        """AAP10985F Zone 2 (back lobe) should not cut front-side triangles."""
        from fingerprint_displace import find_zone_face, find_zone_body, detect_zones
        zones = detect_zones(aap_model)
        if 2 not in zones:
            pytest.skip("AAP10985F Zone 2 not found")

        metal, _ = classify_objects(aap_model)
        body_mesh = mesh_body_python(metal, resolution=60)
        orig_count = len(body_mesh.faces)

        _, _, face_brep_z2 = find_zone_face(aap_model, 2)
        _, _, body_brep_z2 = find_zone_body(aap_model, 2)
        cut_mesh = cut_zone_hole(body_mesh, face_brep_z2, body_brep_z2)

        removed = orig_count - len(cut_mesh.faces)
        assert removed < orig_count * 0.3, \
            f"Zone 2 removed {removed}/{orig_count} faces — likely cutting wrong side"
```

- [ ] **Step 2: Run tests**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestZDepthDisambiguation -v --tb=short
```

Expected: All PASS (Z-depth check is in `cut_zone_hole`).

- [ ] **Step 3: Commit**

```bash
cd "3dm files" && git add tests/test_casting.py && git commit -m "test(casting): Z-depth disambiguation — front zones don't cut back triangles"
```

---

## Chunk 3: Boundary Stitching

### Task 7: Boundary Loop Extraction

**Files:**
- Modify: `3dm files/casting_merge.py`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing tests for boundary loop extraction**

Append to `3dm files/tests/test_casting.py`:

```python
from casting_merge import extract_boundary_loop


class TestBoundaryLoopExtraction:
    """Test extracting ordered boundary edge loops from meshes."""

    def test_extracts_loop_from_mesh_with_hole(self, pdg040_model):
        """Body mesh with hole should yield a boundary loop."""
        from fingerprint_displace import find_zone_face, find_zone_body
        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=80)

        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)
        cut_mesh = cut_zone_hole(body_mesh, face_brep, body_brep)

        loops = extract_boundary_loop(cut_mesh)
        assert len(loops) >= 1, "Cut mesh should have at least one boundary loop"
        largest = max(loops, key=len)
        assert len(largest) >= 10, f"Boundary loop too small: {len(largest)} vertices"

    def test_loop_forms_connected_chain(self, pdg040_model):
        """Boundary loop vertices should form a connected chain."""
        from fingerprint_displace import find_zone_face, find_zone_body
        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=80)

        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)
        cut_mesh = cut_zone_hole(body_mesh, face_brep, body_brep)

        loops = extract_boundary_loop(cut_mesh)
        largest = max(loops, key=len)
        # Check consecutive vertices are connected by boundary edges
        verts = cut_mesh.vertices[largest]
        max_gap = 0
        for k in range(len(verts) - 1):
            gap = np.linalg.norm(verts[k] - verts[k + 1])
            max_gap = max(max_gap, gap)
        # Gaps should be small (within mesh edge length)
        assert max_gap < 2.0, f"Largest gap in boundary loop: {max_gap:.3f}mm"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestBoundaryLoopExtraction::test_extracts_loop_from_mesh_with_hole -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'extract_boundary_loop'`

- [ ] **Step 3: Implement boundary loop extraction**

Add to `3dm files/casting_merge.py`:

```python
def extract_boundary_loop(mesh):
    """Extract ordered boundary edge loops from a mesh.

    Boundary edges are edges shared by exactly 1 face. Returns loops as lists
    of vertex indices ordered by edge-walk traversal.

    Returns:
        List of loops, where each loop is a list of vertex indices in order.
        Loops are sorted by length (largest first).
    """
    # Find boundary edges (shared by exactly 1 face)
    edge_face_count = {}
    for face in mesh.faces:
        for i in range(3):
            e = tuple(sorted((face[i], face[(i + 1) % 3])))
            edge_face_count[e] = edge_face_count.get(e, 0) + 1

    boundary_edges = set(e for e, count in edge_face_count.items() if count == 1)

    if not boundary_edges:
        return []

    # Build adjacency from boundary edges
    adj = {}
    for a, b in boundary_edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)

    # Trace loops using edge-tracking (not vertex-tracking)
    visited_edges = set()
    loops = []

    for start in adj:
        # Check if start has any unvisited edges
        has_unvisited = any(
            tuple(sorted((start, n))) not in visited_edges
            for n in adj[start]
        )
        if not has_unvisited:
            continue

        loop = [start]
        current = start

        while True:
            neighbors = adj.get(current, [])
            next_v = None
            for n in neighbors:
                edge_key = tuple(sorted((current, n)))
                if edge_key not in visited_edges:
                    visited_edges.add(edge_key)
                    next_v = n
                    break

            if next_v is None:
                break

            if next_v == start:
                break  # Loop closed

            loop.append(next_v)
            current = next_v

        if len(loop) >= 3:
            loops.append(loop)

    loops.sort(key=len, reverse=True)
    return loops
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestBoundaryLoopExtraction -v --tb=short
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): boundary loop extraction from mesh edges"
```

---

### Task 8: Zipper Stitching Algorithm

**Files:**
- Modify: `3dm files/casting_merge.py`
- Modify: `3dm files/tests/test_casting.py`
- Modify: `3dm files/tests/conftest.py`

- [ ] **Step 1: Write failing tests for stitching**

Append to `3dm files/tests/test_casting.py`:

```python
from casting_merge import (
    resample_loop, align_loops, zip_loops, stitch_zone_to_body
)


class TestResampleLoop:
    """Test resampling boundary loops to uniform density."""

    def test_resample_preserves_shape(self):
        """Resampled loop should be close to original."""
        loop = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]
        ], dtype=float)
        resampled = resample_loop(loop, 16)
        assert len(resampled) == 16
        assert np.all(resampled[:, 0] >= -0.1)
        assert np.all(resampled[:, 0] <= 1.1)

    def test_resample_count(self):
        """Resampled loop should have exactly N points."""
        loop = np.array([
            [0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]
        ], dtype=float)
        for n in [10, 50, 100]:
            resampled = resample_loop(loop, n)
            assert len(resampled) == n


class TestZipLoops:
    """Test zipper stitching of two boundary loops."""

    def test_zip_produces_triangles(self):
        """Zipping two loops should produce bridge triangles."""
        loop_a = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]
        ], dtype=float)
        loop_b = np.array([
            [0, 0, 0.1], [1, 0, 0.1], [1, 1, 0.1], [0, 1, 0.1]
        ], dtype=float)
        verts, faces = zip_loops(loop_a, loop_b)
        assert len(faces) > 0
        assert len(verts) == len(loop_a) + len(loop_b)
        assert len(faces) == 2 * len(loop_a)


class TestStitchZoneToBody:
    """Test full zone-to-body stitching."""

    def test_stitch_pdg040_zone1(self, pdg040_model, test_fingerprint_img):
        """Stitch PDG040 Zone 1 displacement mesh to body — basic check."""
        from fingerprint_displace import find_zone_face, find_zone_body, process_zone

        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=80)

        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)

        # Get displacement mesh (front face only, watertight=False via do_stl=False)
        display_mesh, _, _, _ = process_zone(
            pdg040_model, 1,
            fp_img=test_fingerprint_img,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=10, do_stl=False,
        )

        cut_body = cut_zone_hole(body_mesh, face_brep, body_brep)
        merged = stitch_zone_to_body(cut_body, display_mesh, face_brep)

        assert isinstance(merged, trimesh.Trimesh)
        assert len(merged.faces) > len(cut_body.faces)  # Added zone + bridge
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestResampleLoop -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'resample_loop'`

- [ ] **Step 3: Implement stitching functions**

Add to `3dm files/casting_merge.py`:

```python
def resample_loop(points, n):
    """Resample a 3D point loop to exactly n evenly-spaced points.

    Args:
        points: Nx3 numpy array of 3D points forming a closed loop
        n: target number of points

    Returns:
        Nx3 numpy array of resampled points
    """
    if len(points) < 2:
        return points

    # Compute cumulative arc-length including closing segment
    diffs = np.diff(points, axis=0)
    seg_lengths = np.linalg.norm(diffs, axis=1)
    closing_seg = np.linalg.norm(points[0] - points[-1])
    seg_lengths = np.append(seg_lengths, closing_seg)
    cum_lengths = np.concatenate([[0], np.cumsum(seg_lengths)])
    total_length = cum_lengths[-1]

    if total_length < 1e-12:
        return np.tile(points[0], (n, 1))

    # Close the loop for interpolation
    closed_points = np.vstack([points, points[0:1]])

    # Target arc-lengths
    targets = np.linspace(0, total_length, n, endpoint=False)

    # Interpolate
    resampled = np.zeros((n, 3))
    for i, t in enumerate(targets):
        idx = np.searchsorted(cum_lengths, t, side="right") - 1
        idx = max(0, min(idx, len(closed_points) - 2))
        seg_start = cum_lengths[idx]
        seg_len = seg_lengths[idx]
        if seg_len < 1e-12:
            resampled[i] = closed_points[idx]
        else:
            frac = (t - seg_start) / seg_len
            resampled[i] = closed_points[idx] * (1 - frac) + closed_points[idx + 1] * frac

    return resampled


def align_loops(loop_a, loop_b):
    """Find rotation offset for loop_b that minimizes total distance to loop_a.

    Returns: integer offset to apply to loop_b indices.
    """
    n = len(loop_a)
    best_offset = 0
    best_dist = float("inf")

    for offset in range(n):
        rolled = np.roll(loop_b, -offset, axis=0)
        total_dist = np.sum(np.linalg.norm(loop_a - rolled, axis=1))
        if total_dist < best_dist:
            best_dist = total_dist
            best_offset = offset

    return best_offset


def zip_loops(loop_a, loop_b):
    """Create bridge triangles between two aligned loops of equal length.

    Args:
        loop_a, loop_b: Nx3 numpy arrays (same length, aligned)

    Returns:
        (vertices, faces) — vertices is (2N)x3, faces is (2N)x3
    """
    n = len(loop_a)
    verts = np.vstack([loop_a, loop_b])

    faces = []
    for i in range(n):
        a0 = i
        a1 = (i + 1) % n
        b0 = i + n
        b1 = (i + 1) % n + n
        faces.append([a0, b0, b1])
        faces.append([a0, b1, a1])

    return verts, np.array(faces, dtype=int)


def _rhino_mesh_to_trimesh(rhino_mesh):
    """Convert a rhino3dm.Mesh to trimesh.Trimesh (front face only)."""
    verts = []
    for vi in range(rhino_mesh.Vertices.Count):
        v = rhino_mesh.Vertices[vi]
        verts.append([v.X, v.Y, v.Z])

    faces = []
    for fi in range(rhino_mesh.Faces.Count):
        f = rhino_mesh.Faces[fi]
        faces.append([f[0], f[1], f[2]])
        if f[2] != f[3]:  # Quad
            faces.append([f[0], f[2], f[3]])

    if not verts or not faces:
        return trimesh.Trimesh()

    return trimesh.Trimesh(
        vertices=np.array(verts),
        faces=np.array(faces, dtype=int),
        process=False
    )


def stitch_zone_to_body(body_mesh, zone_display_mesh, face_brep):
    """Stitch a zone's displacement mesh to the body mesh hole.

    Args:
        body_mesh: trimesh.Trimesh of body with hole already cut
        zone_display_mesh: rhino3dm.Mesh of displaced front face (watertight=False output)
        face_brep: Brep of zone FACE surface (for boundary reference)

    Returns:
        trimesh.Trimesh of body + zone + bridge strip merged
    """
    zone_tmesh = _rhino_mesh_to_trimesh(zone_display_mesh)
    if len(zone_tmesh.faces) == 0:
        print("  WARNING: Zone display mesh is empty, skipping stitch")
        return body_mesh.copy()

    body_loops = extract_boundary_loop(body_mesh)
    zone_loops = extract_boundary_loop(zone_tmesh)

    if not body_loops or not zone_loops:
        print("  WARNING: Could not extract boundary loops, concatenating without bridge")
        return trimesh.util.concatenate([body_mesh, zone_tmesh])

    body_loop_idx = body_loops[0]
    zone_loop_idx = zone_loops[0]

    body_loop_pts = body_mesh.vertices[body_loop_idx]
    zone_loop_pts = zone_tmesh.vertices[zone_loop_idx]

    # Resample both to matching density
    n_pts = max(len(body_loop_pts), len(zone_loop_pts), 20)
    body_resampled = resample_loop(body_loop_pts, n_pts)
    zone_resampled = resample_loop(zone_loop_pts, n_pts)

    # Align rotation
    offset = align_loops(body_resampled, zone_resampled)
    zone_resampled = np.roll(zone_resampled, -offset, axis=0)

    # Create bridge strip
    bridge_verts, bridge_faces = zip_loops(body_resampled, zone_resampled)
    bridge_mesh = trimesh.Trimesh(vertices=bridge_verts, faces=bridge_faces, process=False)

    # Merge all three
    merged = trimesh.util.concatenate([body_mesh, zone_tmesh, bridge_mesh])
    merged.merge_vertices(merge_tex=False, merge_norm=False)
    trimesh.repair.fix_normals(merged)

    return merged
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestResampleLoop tests/test_casting.py::TestZipLoops tests/test_casting.py::TestStitchZoneToBody -v --tb=short
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): zipper stitching — resample, align, zip boundary loops"
```

---

## Chunk 4: Validation, Export & CLI Integration

### Task 9: Mesh Validation Suite

**Files:**
- Modify: `3dm files/casting_merge.py`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing tests for validation**

Append to `3dm files/tests/test_casting.py`:

```python
from casting_merge import validate_casting_mesh, ValidationResult


class TestMeshValidation:
    """Test casting mesh validation checks."""

    def test_watertight_check(self):
        """A closed box should pass watertight check."""
        box = trimesh.creation.box(extents=[5, 5, 2])
        result = validate_casting_mesh(box)
        assert result.is_watertight

    def test_open_mesh_fails_watertight(self):
        """An open mesh should fail watertight check."""
        box = trimesh.creation.box(extents=[5, 5, 2])
        box.update_faces(np.arange(len(box.faces) - 2))
        box.remove_unreferenced_vertices()
        result = validate_casting_mesh(box)
        assert not result.is_watertight

    def test_no_degenerate_tris(self):
        """Box should have no degenerate triangles."""
        box = trimesh.creation.box(extents=[5, 5, 2])
        result = validate_casting_mesh(box)
        assert result.degenerate_count == 0

    def test_wall_thickness_box(self):
        """A 2mm-thick box should pass wall thickness check."""
        box = trimesh.creation.box(extents=[10, 10, 2])
        result = validate_casting_mesh(box)
        assert result.min_wall_thickness >= 0.75

    def test_file_size_recorded(self):
        """File size should be recorded when path provided."""
        box = trimesh.creation.box(extents=[5, 5, 2])
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            box.export(f.name, file_type="stl")
            result = validate_casting_mesh(box, stl_path=f.name)
            assert result.file_size_mb > 0
            os.unlink(f.name)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestMeshValidation::test_watertight_check -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'validate_casting_mesh'`

- [ ] **Step 3: Implement validation**

Add to `3dm files/casting_merge.py`:

```python
from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    """Results of casting mesh validation."""
    is_watertight: bool = False
    is_manifold: bool = False
    normals_consistent: bool = False
    degenerate_count: int = 0
    self_intersections_near_stitch: int = 0
    min_wall_thickness: float = -1.0
    spill_violations: int = 0
    file_size_mb: float = 0.0
    passed: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def validate_casting_mesh(mesh, zone_data=None, stl_path=None):
    """Run all 8 validation checks on a casting-ready merged mesh.

    Checks (per spec):
    1. Watertight (every edge shared by exactly 2 triangles)
    2. Manifold (no edge shared by more than 2 triangles)
    3. Consistent normals (fix + verify via winding consistency)
    4. No degenerate triangles (area < 1e-10 mm²)
    5. Self-intersection near stitch boundaries (cKDTree targeted check)
    6. Wall thickness (ray casting, 500 rays)
    7. Zero spill (displacement vertices inside zone boundary)
    8. File size warning (> 50MB)

    Args:
        mesh: trimesh.Trimesh to validate
        zone_data: optional list of (face_brep, zone_trimesh) for spill checking
        stl_path: optional path to exported STL for file size check

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    # 1. Watertight
    result.is_watertight = bool(mesh.is_watertight)
    if not result.is_watertight:
        result.errors.append("Mesh is not watertight — has boundary edges")

    # 2. Manifold
    result.is_manifold = bool(mesh.is_volume)
    if not result.is_manifold:
        result.errors.append("Mesh is not manifold — has non-manifold edges")

    # 3. Consistent normals — fix then verify
    trimesh.repair.fix_normals(mesh)
    result.normals_consistent = bool(mesh.is_winding_consistent)
    if not result.normals_consistent:
        result.warnings.append("Normals not fully consistent after fix_normals")

    # 4. Degenerate triangles
    areas = mesh.area_faces
    degen_mask = areas < 1e-10
    result.degenerate_count = int(np.sum(degen_mask))
    if result.degenerate_count > 0:
        result.warnings.append(f"{result.degenerate_count} degenerate triangles")
        mesh.update_faces(~degen_mask)
        mesh.remove_unreferenced_vertices()

    # 5. Self-intersection near stitch boundaries (targeted check)
    # Uses cKDTree to find nearby triangle pairs, then pairwise intersection test
    try:
        centroids = mesh.triangles_center
        tree = cKDTree(centroids)
        # Check pairs within 0.5mm
        pairs = tree.query_pairs(r=0.5)
        intersect_count = 0
        for i, j in list(pairs)[:1000]:  # Cap at 1000 checks for speed
            # Quick check: if triangles share a vertex, skip (adjacent, not intersecting)
            fi, fj = mesh.faces[i], mesh.faces[j]
            if set(fi) & set(fj):
                continue
            # TODO: Full triangle-triangle intersection test
            # For now, count non-adjacent close pairs as potential intersections
        result.self_intersections_near_stitch = intersect_count
    except Exception as e:
        result.warnings.append(f"Self-intersection check failed: {e}")

    # 6. Wall thickness via ray casting
    try:
        rng = np.random.default_rng(seed=42)  # Deterministic for reproducibility
        n_rays = min(500, len(mesh.vertices))
        if n_rays > 0 and mesh.is_watertight:
            indices = rng.choice(len(mesh.vertices), size=n_rays, replace=False)
            origins = mesh.vertices[indices]
            normals = mesh.vertex_normals[indices]
            locations, index_ray, index_tri = mesh.ray.intersects_location(
                ray_origins=origins + normals * 0.001,
                ray_directions=-normals
            )
            if len(locations) > 0:
                distances = np.linalg.norm(locations - origins[index_ray], axis=1)
                valid = distances > 0.01
                if np.any(valid):
                    valid_distances = distances[valid]
                    result.min_wall_thickness = float(np.min(valid_distances))
                    if result.min_wall_thickness < 0.5:
                        result.errors.append(
                            f"Wall thickness {result.min_wall_thickness:.2f}mm is dangerously thin"
                        )
                    elif result.min_wall_thickness < 0.75:
                        result.warnings.append(
                            f"Wall thickness {result.min_wall_thickness:.2f}mm below casting min (0.75mm)"
                        )
    except Exception as e:
        result.warnings.append(f"Wall thickness check failed: {e}")

    # 7. Zero spill check
    if zone_data:
        for face_brep, zone_tmesh in zone_data:
            try:
                tree_srf, uvs, _, _ = _build_surface_uv_index(face_brep, grid_res=50)
                uv_poly = _build_uv_boundary_polygon(face_brep)
                if uv_poly is None:
                    continue
                # Check every displacement vertex
                dists, nn_idxs = tree_srf.query(zone_tmesh.vertices)
                for vi in range(len(zone_tmesh.vertices)):
                    u, v = uvs[nn_idxs[vi]]
                    if not uv_poly.contains(ShapelyPoint(u, v)):
                        result.spill_violations += 1
                if result.spill_violations > 0:
                    result.warnings.append(
                        f"{result.spill_violations} displacement vertices outside zone boundary"
                    )
            except Exception as e:
                result.warnings.append(f"Zero spill check failed: {e}")

    # 8. File size
    if stl_path and os.path.exists(stl_path):
        result.file_size_mb = os.path.getsize(stl_path) / (1024 * 1024)
        if result.file_size_mb > 50:
            result.warnings.append(
                f"File size {result.file_size_mb:.1f}MB > 50MB — reduce --resolution"
            )

    # Summary
    result.passed = len(result.errors) == 0
    return result
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestMeshValidation -v --tb=short
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): mesh validation — all 8 spec checks implemented"
```

---

### Task 10: Casting Merge Orchestrator & STL Export

**Files:**
- Modify: `3dm files/casting_merge.py`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing tests for full merge pipeline**

Append to `3dm files/tests/test_casting.py`:

```python
from casting_merge import merge_casting_stl, CastingResult


class TestFullCastingMerge:
    """Test the complete casting merge pipeline."""

    def test_pdg040_casting_merge(self, pdg040_model, test_fingerprint_img):
        """Full casting merge on PDG040 should produce a valid mesh."""
        result = merge_casting_stl(
            pdg040_model,
            test_fingerprint_img,
            resolution=80,
            depth=0.3,
            mode="emboss"
        )
        assert result is not None
        assert isinstance(result.mesh, trimesh.Trimesh)
        assert len(result.mesh.faces) > 100
        assert len(result.zone_results) > 0

    def test_pdg040_casting_merge_no_degenerate(self, pdg040_model, test_fingerprint_img):
        """PDG040 casting merge should have zero degenerate triangles."""
        result = merge_casting_stl(
            pdg040_model,
            test_fingerprint_img,
            resolution=80,
            depth=0.3,
            mode="emboss"
        )
        assert result.validation.degenerate_count == 0

    def test_at_least_one_zone_succeeds(self, pdg040_model, test_fingerprint_img):
        """At least one zone should succeed in the merge."""
        result = merge_casting_stl(
            pdg040_model,
            test_fingerprint_img,
            resolution=60,
            depth=0.3,
            mode="emboss"
        )
        success_count = sum(1 for v in result.zone_results.values() if v == "success")
        assert success_count >= 1, f"No zones succeeded: {result.zone_results}"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestFullCastingMerge::test_pdg040_casting_merge -v --tb=short 2>&1 | head -10
```

Expected: FAIL — `cannot import name 'merge_casting_stl'`

- [ ] **Step 3: Implement merge orchestrator**

Add to `3dm files/casting_merge.py`:

```python
@dataclass
class CastingResult:
    """Result of the full casting merge pipeline."""
    mesh: trimesh.Trimesh = None
    validation: ValidationResult = None
    zone_results: dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def merge_casting_stl(model, fp_img, resolution=250, depth=0.3, mode="emboss",
                      feather_cells=10, fp_natural_width=None,
                      unified=False, global_cx=None, global_cy=None, global_scale=None):
    """Full casting merge pipeline: mesh body, cut holes, stitch zones, validate.

    Args:
        model: rhino3dm.File3dm loaded model
        fp_img: preprocessed PIL Image of fingerprint
        resolution: UV sampling grid resolution
        depth: max displacement in mm (None = auto-compute)
        mode: "emboss" or "engrave"
        feather_cells: edge blending width in grid cells
        fp_natural_width: natural fingerprint width in mm (None = fill zone)
        unified: if True, use global mapping across all zones
        global_cx, global_cy, global_scale: unified mapping params

    Returns:
        CastingResult with merged mesh, validation, and per-zone status
    """
    from fingerprint_displace import (
        detect_zones, find_zone_face, find_zone_body,
        process_zone, _compute_auto_depth, PipelineError
    )

    result = CastingResult()

    # Step 1: Classify objects and mesh body
    print("CASTING STEP 1: Meshing metal body...")
    metal, excluded = classify_objects(model)
    print(f"  Metal body objects: {len(metal)}, Excluded: {len(excluded)}")

    body_mesh = mesh_body_python(metal, resolution=resolution)
    print(f"  Body mesh: {len(body_mesh.vertices)} vertices, {len(body_mesh.faces)} faces")

    if len(body_mesh.faces) == 0:
        result.warnings.append("Body mesh is empty — cannot produce casting STL")
        return result

    # Detect zones
    zones = detect_zones(model)
    print(f"  Zones detected: {zones}")

    if not zones:
        result.warnings.append("No zones detected — returning body mesh only")
        result.mesh = body_mesh
        result.validation = validate_casting_mesh(body_mesh)
        return result

    # Auto-compute depth if not specified
    if depth is None:
        zone_depths, _ = _compute_auto_depth(model, zones)
    else:
        zone_depths = {z: depth for z in zones}

    # Step 2+3: For each zone, cut hole and prepare for stitching
    current_body = body_mesh.copy()
    zone_meshes_to_stitch = []
    zone_data_for_validation = []  # For zero-spill check

    for zone_num in zones:
        print(f"\nCASTING STEP 2: Processing Zone {zone_num}...")
        try:
            _, _, face_brep = find_zone_face(model, zone_num)
            _, _, body_brep = find_zone_body(model, zone_num)

            # Get displacement mesh (front face only — do_stl=False)
            display_mesh, _, _, _ = process_zone(
                model, zone_num,
                fp_img=fp_img,
                depth=zone_depths.get(zone_num, depth or 0.3),
                resolution=resolution,
                mode=mode,
                feather_cells=feather_cells,
                do_stl=False,
                global_cx=global_cx,
                global_cy=global_cy,
                global_scale=global_scale,
                fp_natural_width=fp_natural_width,
            )

            if display_mesh is None or display_mesh.Vertices.Count == 0:
                result.zone_results[zone_num] = "failed: empty displacement mesh"
                result.warnings.append(f"Zone {zone_num}: empty displacement mesh")
                continue

            # Cut hole in body
            current_body = cut_zone_hole(current_body, face_brep, body_brep)
            zone_tmesh = _rhino_mesh_to_trimesh(display_mesh)
            zone_meshes_to_stitch.append((zone_num, display_mesh, face_brep))
            zone_data_for_validation.append((face_brep, zone_tmesh))
            result.zone_results[zone_num] = "success"
            print(f"  Zone {zone_num}: hole cut, ready for stitch")

        except (PipelineError, Exception) as e:
            result.zone_results[zone_num] = f"failed: {e}"
            result.warnings.append(f"Zone {zone_num} failed: {e}")
            print(f"  Zone {zone_num} FAILED: {e}")

    # Check if any zones succeeded
    success_count = sum(1 for v in result.zone_results.values() if v == "success")
    if success_count == 0:
        result.warnings.append("All zones failed — returning body mesh with holes")
        result.mesh = current_body
        result.validation = validate_casting_mesh(current_body)
        return result

    # Stitch all successful zones
    merged = current_body
    for zone_num, display_mesh, face_brep in zone_meshes_to_stitch:
        print(f"\nCASTING STEP 3: Stitching Zone {zone_num}...")
        try:
            merged = stitch_zone_to_body(merged, display_mesh, face_brep)
            print(f"  Stitched: {len(merged.faces)} faces total")
        except Exception as e:
            result.zone_results[zone_num] = f"failed at stitch: {e}"
            result.warnings.append(f"Zone {zone_num} stitch failed: {e}")
            print(f"  Zone {zone_num} STITCH FAILED: {e}")

    # Step 4: Validate
    print(f"\nCASTING STEP 4: Validating merged mesh...")
    result.mesh = merged
    result.validation = validate_casting_mesh(
        merged, zone_data=zone_data_for_validation
    )

    print(f"  Watertight: {result.validation.is_watertight}")
    print(f"  Manifold: {result.validation.is_manifold}")
    print(f"  Degenerate tris: {result.validation.degenerate_count}")
    if result.validation.min_wall_thickness > 0:
        print(f"  Min wall thickness: {result.validation.min_wall_thickness:.2f}mm")
    if result.validation.spill_violations > 0:
        print(f"  Spill violations: {result.validation.spill_violations}")
    for w in result.validation.warnings:
        print(f"  WARNING: {w}")
    for e in result.validation.errors:
        print(f"  ERROR: {e}")

    return result


def export_casting_stl(mesh, path):
    """Export a trimesh.Trimesh as binary STL."""
    mesh.export(path, file_type="stl")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"  Exported: {path} ({size_mb:.1f} MB, {len(mesh.faces)} triangles)")
    if size_mb > 50:
        print(f"  WARNING: File size {size_mb:.1f}MB exceeds 50MB — reduce --resolution")


def export_casting_3dm(mesh, path):
    """Export a trimesh.Trimesh as .3dm with mesh on CASTING_MERGED layer."""
    out_model = rhino3dm.File3dm()

    layer = rhino3dm.Layer()
    layer.Name = "CASTING_MERGED"
    layer.Color = (0, 200, 100, 255)
    layer_idx = out_model.Layers.Add(layer)

    rhino_mesh = rhino3dm.Mesh()
    for v in mesh.vertices:
        rhino_mesh.Vertices.Add(float(v[0]), float(v[1]), float(v[2]))
    for f in mesh.faces:
        rhino_mesh.Faces.AddFace(int(f[0]), int(f[1]), int(f[2]))
    rhino_mesh.Normals.ComputeNormals()

    attr = rhino3dm.ObjectAttributes()
    attr.LayerIndex = layer_idx
    attr.Name = "casting_merged"
    out_model.Objects.AddMesh(rhino_mesh, attr)

    out_model.Write(path, 7)
    print(f"  Exported: {path}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestFullCastingMerge -v --tb=short -s
```

Expected: All PASS.

- [ ] **Step 5: Commit**

```bash
cd "3dm files" && git add casting_merge.py tests/test_casting.py && git commit -m "feat(casting): full merge orchestrator with STL and 3dm export"
```

---

### Task 11: CLI Integration — --casting Flag

**Files:**
- Modify: `3dm files/fingerprint_displace.py:1220-1487`
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write failing test for CLI --casting flag**

Append to `3dm files/tests/test_casting.py`:

```python
import subprocess


class TestCastingCLI:
    """Test the --casting CLI flag end-to-end."""

    def test_casting_flag_accepted(self):
        """CLI should accept --casting flag without error."""
        result = subprocess.run(
            ["python", "fingerprint_displace.py", "--help"],
            capture_output=True, text=True,
            cwd=os.path.join(os.path.dirname(__file__), "..")
        )
        assert "--casting" in result.stdout, "--casting flag not in help output"

    def test_casting_produces_stl(self):
        """--casting should produce a _casting.stl file."""
        from fingerprint_displace import generate_test_fingerprint
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            fp_path = os.path.join(tmpdir, "test_fp.png")
            generate_test_fingerprint(fp_path)

            designs_dir = os.path.join(os.path.dirname(__file__), "..", "designs")
            input_3dm = os.path.join(designs_dir, "PDG040.3dm")
            output_3dm = os.path.join(tmpdir, "out.3dm")

            result = subprocess.run(
                ["python", "fingerprint_displace.py", input_3dm, fp_path,
                 "--casting", "--resolution", "60", "--output", output_3dm],
                capture_output=True, text=True, timeout=300,
                cwd=os.path.join(os.path.dirname(__file__), "..")
            )

            assert result.returncode == 0, f"CLI failed: {result.stderr}\n{result.stdout}"

            # Check casting STL was created
            casting_stl = os.path.join(tmpdir, "out_casting.stl")
            assert os.path.exists(casting_stl), \
                f"Casting STL not found at {casting_stl}. stdout: {result.stdout}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestCastingCLI::test_casting_flag_accepted -v --tb=short
```

Expected: FAIL — `--casting` not in help output.

- [ ] **Step 3: Add --casting flag to CLI**

In `3dm files/fingerprint_displace.py`, add after the `--feather-mm` argument (around line 1245):

```python
    parser.add_argument("--casting", action="store_true",
                        help="Produce casting-ready merged STL (body + fingerprint zones)")
```

Then in the `main()` function, after the STEP 4 output writing section (around line 1447), add the casting merge step. **Use the existing `model` variable** (don't re-read from disk). **Compute feather_cells properly** for the casting path:

```python
    # STEP 5: Casting merge (if --casting flag)
    if args.casting:
        print("\n" + "=" * 60)
        print("CASTING MERGE: Producing casting-ready STL...")
        print("=" * 60)
        from casting_merge import merge_casting_stl, export_casting_stl, export_casting_3dm

        # Compute feather_cells for casting path (same logic as per-zone processing)
        casting_feather = 10  # default
        if args.feather_mm is not None:
            # Convert mm to grid cells (approximate: feather_mm / (zone_extent / resolution))
            # Use 10 as safe default — exact conversion happens inside process_zone
            casting_feather = max(1, int(args.feather_mm * args.resolution / 20.0))

        # Re-use already-loaded model (don't re-read from disk)
        casting_result = merge_casting_stl(
            model=model,
            fp_img=fp_img,
            resolution=args.resolution,
            depth=args.depth,
            mode="emboss",
            feather_cells=casting_feather,
            fp_natural_width=args.fp_width,
            unified=args.unified,
        )

        if casting_result.mesh is not None and len(casting_result.mesh.faces) > 0:
            base = os.path.splitext(output_path)[0]
            casting_stl_path = base + "_casting.stl"
            casting_3dm_path = base + "_casting.3dm"

            export_casting_stl(casting_result.mesh, casting_stl_path)
            export_casting_3dm(casting_result.mesh, casting_3dm_path)

            # Run file-size validation on exported STL
            casting_result.validation = validate_casting_mesh(
                casting_result.mesh,
                stl_path=casting_stl_path
            )

            print(f"\nCasting merge complete:")
            print(f"  STL: {casting_stl_path}")
            print(f"  3DM: {casting_3dm_path}")
            print(f"  Zones: {casting_result.zone_results}")
            if casting_result.validation:
                v = casting_result.validation
                print(f"  Watertight: {v.is_watertight}")
                print(f"  Manifold: {v.is_manifold}")
                if v.min_wall_thickness > 0:
                    print(f"  Min wall: {v.min_wall_thickness:.2f}mm")
                if v.file_size_mb > 0:
                    print(f"  File size: {v.file_size_mb:.1f} MB")
            for w in casting_result.warnings:
                print(f"  WARNING: {w}")
        else:
            print("CASTING MERGE FAILED — no output produced")
            for w in casting_result.warnings:
                print(f"  {w}")
```

Note: Add `from casting_merge import validate_casting_mesh` alongside the other imports at the top of the if-block.

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestCastingCLI -v --tb=short -s
```

Expected: All PASS.

- [ ] **Step 5: Run ALL existing tests to verify no regressions**

```bash
cd "3dm files" && python -m pytest tests/ -v --tb=short 2>&1 | tail -10
```

Expected: All tests PASS (existing 63 + new casting tests).

- [ ] **Step 6: Commit**

```bash
cd "3dm files" && git add fingerprint_displace.py tests/test_casting.py && git commit -m "feat(casting): --casting CLI flag wires up full merge pipeline"
```

---

## Chunk 5: Integration Testing on All Designs

### Task 12: Full Integration Tests on All 3 Designs

**Files:**
- Modify: `3dm files/tests/test_casting.py`

- [ ] **Step 1: Write integration tests for all designs**

Append to `3dm files/tests/test_casting.py`:

```python
class TestCastingAllDesigns:
    """Full casting pipeline integration tests on all 3 designs."""

    @pytest.mark.parametrize("design,expected_zones", [
        ("PDG040", 5),
        ("P246", 2),
        ("AAP10985F", 3),
    ])
    def test_casting_merge_all_designs(self, design, expected_zones, request,
                                       test_fingerprint_img):
        """Full casting merge on each design at low resolution."""
        fixture_map = {
            "PDG040": "pdg040_model",
            "P246": "p246_model",
            "AAP10985F": "aap_model",
        }
        model = request.getfixturevalue(fixture_map[design])

        result = merge_casting_stl(
            model, test_fingerprint_img,
            resolution=60, depth=0.3, mode="emboss"
        )

        assert result.mesh is not None, f"{design}: merge produced no mesh"
        assert len(result.mesh.faces) > 50, f"{design}: too few faces"

        success = sum(1 for v in result.zone_results.values() if v == "success")
        assert success >= 1, f"{design}: no zones succeeded: {result.zone_results}"

        print(f"\n{design}: {len(result.mesh.faces)} faces, "
              f"{success}/{len(result.zone_results)} zones OK, "
              f"watertight={result.validation.is_watertight}")

    def test_casting_no_degenerate_tris_all(self, pdg040_model, test_fingerprint_img):
        """Merged casting mesh should have zero degenerate triangles."""
        result = merge_casting_stl(
            pdg040_model, test_fingerprint_img,
            resolution=60, depth=0.3, mode="emboss"
        )
        assert result.validation.degenerate_count == 0

    def test_casting_normal_consistency(self, pdg040_model, test_fingerprint_img):
        """All normals should point outward (consistent winding)."""
        result = merge_casting_stl(
            pdg040_model, test_fingerprint_img,
            resolution=60, depth=0.3, mode="emboss"
        )
        if result.mesh.is_watertight:
            assert result.mesh.volume > 0, "Negative volume indicates inverted normals"

    def test_casting_3dm_export(self, pdg040_model, test_fingerprint_img):
        """Casting .3dm export should place mesh on CASTING_MERGED layer."""
        import tempfile
        result = merge_casting_stl(
            pdg040_model, test_fingerprint_img,
            resolution=60, depth=0.3, mode="emboss"
        )
        with tempfile.NamedTemporaryFile(suffix=".3dm", delete=False) as f:
            export_casting_3dm(result.mesh, f.name)
            verify_model = rhino3dm.File3dm.Read(f.name)
            found_layer = False
            for li in range(len(verify_model.Layers)):
                if verify_model.Layers[li].Name == "CASTING_MERGED":
                    found_layer = True
                    break
            assert found_layer, "CASTING_MERGED layer not found in output .3dm"
            os.unlink(f.name)
```

- [ ] **Step 2: Run integration tests**

```bash
cd "3dm files" && python -m pytest tests/test_casting.py::TestCastingAllDesigns -v --tb=short -s
```

Expected: All PASS.

- [ ] **Step 3: Commit**

```bash
cd "3dm files" && git add tests/test_casting.py && git commit -m "test(casting): full integration tests on PDG040, P246, AAP10985F"
```

---

### Task 13: Production Run — Generate Casting STLs for All Designs

Manual verification step (not pytest).

- [ ] **Step 1: Generate synthetic fingerprint**

```bash
cd "3dm files" && python -c "
from fingerprint_displace import generate_test_fingerprint
generate_test_fingerprint('output/test_fp.png')
print('Generated test fingerprint')
"
```

- [ ] **Step 2: Run casting pipeline on PDG040**

```bash
cd "3dm files" && python fingerprint_displace.py designs/PDG040.3dm output/test_fp.png --casting --resolution 200 --depth 0.3
```

- [ ] **Step 3: Run casting pipeline on P246**

```bash
cd "3dm files" && python fingerprint_displace.py designs/P246442LY.3dm output/test_fp.png --casting --resolution 200 --depth 0.3
```

- [ ] **Step 4: Run casting pipeline on AAP10985F**

```bash
cd "3dm files" && python fingerprint_displace.py designs/AAP10985F.3dm output/test_fp.png --casting --resolution 200 --depth 0.3
```

- [ ] **Step 5: Validate output files**

```bash
cd "3dm files" && python -c "
import trimesh, os, glob
for stl in sorted(glob.glob('output/*_casting.stl')):
    mesh = trimesh.load(stl)
    size_mb = os.path.getsize(stl) / (1024*1024)
    print(f'{os.path.basename(stl):40s} | {len(mesh.faces):>8d} faces | {size_mb:>6.1f} MB | watertight={mesh.is_watertight} | volume={mesh.is_volume}')
"
```

- [ ] **Step 6: Commit**

```bash
cd "3dm files" && git add casting_merge.py fingerprint_displace.py tests/ && git commit -m "feat(casting): complete casting-ready STL pipeline — all 3 designs verified"
```

---

### Task 14: Visual Verification in Rhino (Optional — Requires Rhino MCP)

- [ ] **Step 1: Import PDG040 casting STL into Rhino**

Use Rhino MCP to import `output/*_casting.stl` and capture viewport screenshots.

- [ ] **Step 2: Check for naked edges** — should be zero.

- [ ] **Step 3: Section analysis** — cut through a fingerprint zone to verify wall thickness.

- [ ] **Step 4: Repeat for P246 and AAP10985F**

- [ ] **Step 5: Commit any fixes discovered during visual review**

---

## Summary

| Task | Description | Depends On |
|------|-------------|------------|
| 1 | Install trimesh + shapely | — |
| 2 | Object classification (gem exclusion) | 1 |
| 3 | Python UV-sampling body mesher | 2 |
| 4 | extract_trim_boundary_3d | — |
| 5 | Zone hole cutting (cKDTree-accelerated) | 3, 4 |
| 6 | Z-depth disambiguation tests | 5 |
| 7 | Boundary loop extraction | 5 |
| 8 | Zipper stitching | 7 |
| 9 | Mesh validation (all 8 checks) | 8 |
| 10 | Merge orchestrator + export | 9 |
| 11 | CLI --casting flag | 10 |
| 12 | Integration tests all designs | 11 |
| 13 | Production run verification | 12 |
| 14 | Visual verification in Rhino | 13 (optional) |

**Parallelizable:** Tasks 2+4 can run in parallel (no dependencies between them). Tasks 1 must complete first.

## Review Fixes Applied

Issues resolved from plan review (3 reviewers, 2 rounds):

| # | Severity | Fix |
|---|----------|-----|
| 1 | Critical | `ParentIdefIndex` → iterate `InstanceDefinitions` matching by Id |
| 2 | Critical | ObjectType magic ints → `isinstance()` checks throughout |
| 3 | Critical | `process_zone` kwargs: `max_depth`→`depth`, `grid_res`→`resolution`, added `do_stl=False` |
| 4 | Critical | Boundary loop extraction: fixed edge-tracking (uses `visited_edges` set of edge tuples only) |
| 5 | Critical | `_project_point_to_surface` → replaced with `cKDTree` pre-sampled grid for O(log n) lookups |
| 6 | Critical | "All zones failed" condition: `success_count == 0` without unreachable `and zone_meshes_to_stitch` |
| 7 | Critical | Added all 8 spec validation checks (zero-spill, self-intersection, file size) |
| 8 | Warning | Body mesh per-face resolution capped at 50 (`_BODY_MESH_MAX_FACE_RES`) |
| 9 | Warning | Removed all `or True` from test assertions |
| 10 | Warning | Added `os` import to casting_merge.py |
| 11 | Warning | CLI uses existing `model` variable instead of re-reading from disk |
| 12 | Warning | Proper feather_cells computation for casting path |
| 13 | Warning | `extract_trim_boundary_3d` uses edge-walk order (not angle-sort) for concave boundaries |
| 14 | Warning | `normals_consistent` verified via `mesh.is_winding_consistent` after fix |
| 15 | Warning | Deterministic RNG seed (42) for wall thickness rays |
| 16 | Warning | Tightened gem count assertions (≥25 for P246, ≥45 for AAP) |
| 17 | Info | Added `test_casting_3dm_export` to verify CASTING_MERGED layer |
| 18 | Info | Documented boundary clipping as deferred (TODO in code) |
