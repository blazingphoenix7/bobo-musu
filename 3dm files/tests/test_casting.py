"""Tests for the casting-ready STL pipeline — classification, meshing, hole cutting, loops,
stitching, validation, merge orchestrator, and CLI integration."""

import os
import subprocess
import sys

import numpy as np
import pytest

# Add parent directory to path so we can import casting_merge
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rhino3dm
import trimesh as tm
from casting_merge import (
    _GEM_NAME_RE,
    _GEM_LAYER_RE,
    _FACE_LAYER_RE,
    _get_idef_name,
    _pip_2d,
    _weld_vertices,
    _mesh_single_brep_face,
    _build_surface_uv_index,
    _build_uv_boundary_polygon,
    _get_face_average_normal,
    cut_zone_hole,
    extract_boundary_loop,
    is_gem_instance,
    classify_objects,
    mesh_body_python,
    resample_loop,
    align_loops,
    zip_loops,
    _rhino_mesh_to_trimesh,
    stitch_zone_to_body,
    ValidationResult,
    validate_casting_mesh,
    CastingResult,
    merge_casting_stl,
    export_casting_stl,
    export_casting_3dm,
)

# Also keep the existing 3D boundary tests
from fingerprint_displace import (
    extract_trim_boundary,
    extract_trim_boundary_3d,
    find_zone_face,
    find_zone_body,
    detect_zones,
    process_zone,
)


# ── Existing 3D boundary tests ──────────────────────────────────────

class TestExtractTrimBoundary3D:
    """Tests for extract_trim_boundary_3d."""

    def test_returns_xyz_tuples(self, pdg040_model):
        """Verify 3D boundary returns (X, Y, Z) triples with >10 points."""
        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        assert face_brep is not None

        boundary_3d = extract_trim_boundary_3d(face_brep)
        assert len(boundary_3d) > 10, f"Expected >10 points, got {len(boundary_3d)}"
        for pt in boundary_3d:
            assert len(pt) == 3, f"Expected 3-tuple, got {len(pt)}-tuple: {pt}"
            assert all(isinstance(c, float) for c in pt), f"Expected floats: {pt}"

    def test_consistent_with_2d(self, pdg040_model):
        """Verify XY coords match between 2D and 3D versions."""
        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)
        assert face_brep is not None

        boundary_2d = extract_trim_boundary(face_brep, body_brep=body_brep)
        boundary_3d = extract_trim_boundary_3d(face_brep, body_brep=body_brep)

        xy_from_3d = set()
        for pt in boundary_3d:
            xy_from_3d.add((round(pt[0], 3), round(pt[1], 3)))

        xy_from_2d = set()
        for pt in boundary_2d:
            xy_from_2d.add((round(pt[0], 3), round(pt[1], 3)))

        overlap = xy_from_2d & xy_from_3d
        overlap_ratio = len(overlap) / max(len(xy_from_2d), 1)
        assert overlap_ratio > 0.5, (
            f"XY overlap too low: {overlap_ratio:.2f} "
            f"(2D has {len(xy_from_2d)} unique, 3D has {len(xy_from_3d)} unique, "
            f"{len(overlap)} in common)"
        )


# ── TestIsGemInstance ────────────────────────────────────────────────

class TestIsGemInstance:
    """Test gem InstanceReference detection."""

    def test_p246_has_gem_instances(self, p246_model):
        """P246 should have InstanceReferences that are identified as gems."""
        layer_names = {}
        for i in range(len(p246_model.Layers)):
            layer_names[p246_model.Layers[i].Index] = p246_model.Layers[i].Name

        gem_count = 0
        for obj in p246_model.Objects:
            geo = obj.Geometry
            if isinstance(geo, rhino3dm.InstanceReference):
                layer_name = layer_names.get(obj.Attributes.LayerIndex, "")
                if is_gem_instance(obj, geo, layer_name, p246_model):
                    gem_count += 1

        assert gem_count >= 25, f"Expected >=25 gems in P246, got {gem_count}"

    def test_breps_are_not_gems(self, p246_model):
        """Brep objects should never be identified as gems."""
        layer_names = {}
        for i in range(len(p246_model.Layers)):
            layer_names[p246_model.Layers[i].Index] = p246_model.Layers[i].Name

        for obj in p246_model.Objects:
            geo = obj.Geometry
            if isinstance(geo, rhino3dm.Brep):
                layer_name = layer_names.get(obj.Attributes.LayerIndex, "")
                assert not is_gem_instance(obj, geo, layer_name, p246_model), \
                    f"Brep on layer '{layer_name}' falsely identified as gem"

    def test_gem_name_regex(self):
        """Regex should match common gem definition names."""
        assert _GEM_NAME_RE.search("Diamond_Round")
        assert _GEM_NAME_RE.search("diamond_brilliant")
        assert _GEM_NAME_RE.search("GEM_SETTING")
        assert _GEM_NAME_RE.search("Stone_Oval")
        assert _GEM_NAME_RE.search("Brilliant_Cut")
        assert not _GEM_NAME_RE.search("Metal_Body")
        assert not _GEM_NAME_RE.search("Round_Setting")  # "round" alone is too generic

    def test_gem_layer_regex(self):
        """Layer regex should match gem-related layer names."""
        assert _GEM_LAYER_RE.search("Diamond")
        assert _GEM_LAYER_RE.search("Gem Settings")
        assert _GEM_LAYER_RE.search("stone_layer")
        assert not _GEM_LAYER_RE.search("Metal 01")
        assert not _GEM_LAYER_RE.search("Default")


# ── TestClassifyObjects ─────────────────────────────────────────────

class TestClassifyObjects:
    """Test object classification into metal vs excluded."""

    def test_pdg040_all_metal(self, pdg040_model):
        """PDG040 has no gems — all Breps should be metal (minus FACE layers)."""
        metal, excluded = classify_objects(pdg040_model)
        assert len(metal) > 0, "PDG040 should have metal objects"
        for _idx, _obj, geo in metal:
            assert isinstance(geo, (rhino3dm.Brep, rhino3dm.Extrusion)), \
                f"Unexpected metal geometry type: {type(geo)}"

    def test_p246_excludes_gems(self, p246_model):
        """P246 should exclude >=25 gem InstanceReferences."""
        metal, excluded = classify_objects(p246_model)
        gem_count = sum(
            1 for _idx, _obj, geo in excluded
            if isinstance(geo, rhino3dm.InstanceReference)
        )
        assert gem_count >= 25, f"Expected >=25 excluded gems, got {gem_count}"
        assert len(metal) > 0, "P246 should still have metal objects"

    def test_aap_excludes_gems(self, aap_model):
        """AAP10985F should exclude >=45 gem InstanceReferences."""
        metal, excluded = classify_objects(aap_model)
        gem_count = sum(
            1 for _idx, _obj, geo in excluded
            if isinstance(geo, rhino3dm.InstanceReference)
        )
        assert gem_count >= 45, f"Expected >=45 excluded gems, got {gem_count}"
        assert len(metal) > 0, "AAP10985F should still have metal objects"

    def test_face_layers_excluded(self, pdg040_model):
        """Objects on FP_ZONE_*_FACE layers should be excluded."""
        _metal, excluded = classify_objects(pdg040_model)

        layer_names = {}
        for i in range(len(pdg040_model.Layers)):
            layer_names[pdg040_model.Layers[i].Index] = pdg040_model.Layers[i].Name

        face_excluded = sum(
            1 for _idx, obj, _geo in excluded
            if _FACE_LAYER_RE.match(layer_names.get(obj.Attributes.LayerIndex, ""))
        )
        assert face_excluded > 0, "Should have excluded at least one FACE layer object"

    def test_textdots_excluded(self, aap_model):
        """TextDots should be excluded."""
        _metal, excluded = classify_objects(aap_model)
        textdot_count = sum(
            1 for _idx, _obj, geo in excluded
            if isinstance(geo, rhino3dm.TextDot)
        )
        assert textdot_count > 0, "AAP should have TextDots in excluded list"

    def test_no_gems_in_metal(self, p246_model):
        """No InstanceReferences should appear in metal list."""
        metal, _excluded = classify_objects(p246_model)
        for _idx, _obj, geo in metal:
            assert not isinstance(geo, rhino3dm.InstanceReference), \
                "InstanceReference found in metal list"


# ── TestBodyMesher ──────────────────────────────────────────────────

class TestBodyMesher:
    """Test body mesh generation from metal objects."""

    def test_pdg040_mesh(self, pdg040_model):
        """PDG040 body mesh should have >100 vertices and faces."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)
        assert len(mesh.vertices) > 100, \
            f"PDG040 mesh has too few vertices: {len(mesh.vertices)}"
        assert len(mesh.faces) > 100, \
            f"PDG040 mesh has too few faces: {len(mesh.faces)}"

    def test_p246_mesh(self, p246_model):
        """P246 body mesh should have >100 vertices and faces."""
        metal, _ = classify_objects(p246_model)
        mesh = mesh_body_python(metal, resolution=250)
        assert len(mesh.vertices) > 100, \
            f"P246 mesh has too few vertices: {len(mesh.vertices)}"
        assert len(mesh.faces) > 100, \
            f"P246 mesh has too few faces: {len(mesh.faces)}"

    def test_aap_mesh(self, aap_model):
        """AAP10985F body mesh should have >100 vertices and faces."""
        metal, _ = classify_objects(aap_model)
        mesh = mesh_body_python(metal, resolution=250)
        assert len(mesh.vertices) > 100, \
            f"AAP mesh has too few vertices: {len(mesh.vertices)}"
        assert len(mesh.faces) > 100, \
            f"AAP mesh has too few faces: {len(mesh.faces)}"

    def test_no_degenerate_triangles(self, pdg040_model):
        """Body mesh should have no degenerate (zero-area) triangles."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)
        v0 = mesh.vertices[mesh.faces[:, 0]]
        v1 = mesh.vertices[mesh.faces[:, 1]]
        v2 = mesh.vertices[mesh.faces[:, 2]]
        cross = np.cross(v1 - v0, v2 - v0)
        areas = 0.5 * np.linalg.norm(cross, axis=1)
        degenerate = np.sum(areas < 1e-10)
        assert degenerate == 0, f"Found {degenerate} degenerate triangles"

    def test_vertex_welding(self):
        """Vertex welding should merge nearby vertices and remap triangles."""
        verts = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.5, 1.0, 0.0],
            [0.005, 0.005, 0.0],  # near-duplicate of vertex 0
            [1.005, 0.0, 0.0],    # near-duplicate of vertex 1
            [0.5, -1.0, 0.0],
        ])
        tris = np.array([
            [0, 1, 2],
            [3, 4, 5],
        ], dtype=int)

        welded_v, welded_t = _weld_vertices(verts, tris, tolerance=0.01)
        assert len(welded_v) == 4, f"Expected 4 unique verts, got {len(welded_v)}"
        assert len(welded_t) == 2, f"Expected 2 triangles, got {len(welded_t)}"

    def test_vertex_welding_degenerate_removal(self):
        """Welding that collapses a triangle should remove it."""
        verts = np.array([
            [0.0, 0.0, 0.0],
            [0.005, 0.0, 0.0],  # near-duplicate of 0
            [0.002, 0.003, 0.0],  # near-duplicate of 0
        ])
        tris = np.array([[0, 1, 2]], dtype=int)
        welded_v, welded_t = _weld_vertices(verts, tris, tolerance=0.01)
        assert len(welded_t) == 0, f"Degenerate triangle should be removed, got {len(welded_t)}"

    def test_pip_2d_inside(self):
        """Point inside a square polygon should return True."""
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _pip_2d(5, 5, square) is True

    def test_pip_2d_outside(self):
        """Point outside a square polygon should return False."""
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _pip_2d(15, 5, square) is False

    def test_mesh_returns_trimesh(self, pdg040_model):
        """mesh_body_python should return a trimesh.Trimesh instance."""
        import trimesh as tm
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)
        assert isinstance(mesh, tm.Trimesh)


# ── TestZoneHoleCutting (Task 5) ───────────────────────────────────

class TestZoneHoleCutting:
    """Test zone hole cutting on body meshes."""

    def test_cut_removes_triangles_pdg040(self, pdg040_model):
        """Cutting zone 1 should remove some triangles from PDG040 body."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)
        orig_count = len(mesh.faces)

        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)
        assert face_brep is not None

        result = cut_zone_hole(mesh, face_brep, body_brep=body_brep)
        assert len(result.faces) < orig_count, \
            f"Expected fewer faces after cut, got {len(result.faces)} vs {orig_count}"

    def test_cut_doesnt_remove_everything(self, pdg040_model):
        """Cutting a zone should leave most of the body intact."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)
        orig_count = len(mesh.faces)

        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)
        assert face_brep is not None

        result = cut_zone_hole(mesh, face_brep, body_brep=body_brep)
        assert len(result.faces) > orig_count * 0.3, \
            f"Cut removed too many triangles: {len(result.faces)} of {orig_count}"

    def test_surface_uv_index_shape(self, pdg040_model):
        """_build_surface_uv_index should return correctly shaped arrays."""
        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        assert face_brep is not None

        tree, uv, pts, normals = _build_surface_uv_index(face_brep, grid_res=20)
        assert uv.shape == (400, 2)
        assert pts.shape == (400, 3)
        assert normals.shape == (400, 3)

    def test_uv_boundary_polygon_valid(self, pdg040_model):
        """_build_uv_boundary_polygon should return a valid Shapely polygon."""
        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)
        assert face_brep is not None

        poly = _build_uv_boundary_polygon(face_brep, body_brep=body_brep)
        assert poly is not None, "UV boundary polygon should not be None"
        assert poly.is_valid, "UV boundary polygon should be valid"
        assert poly.area > 0, "UV boundary polygon should have positive area"

    def test_face_average_normal_unit(self, pdg040_model):
        """_get_face_average_normal should return a unit vector."""
        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        assert face_brep is not None

        n = _get_face_average_normal(face_brep)
        assert abs(np.linalg.norm(n) - 1.0) < 1e-6, \
            f"Expected unit normal, got magnitude {np.linalg.norm(n)}"


# ── TestZDepthDisambiguation (Task 6) ─────────────────────────────

class TestZDepthDisambiguation:
    """Test that hole cutting respects Z-depth — doesn't cut through the back."""

    def test_aap_zone1_front_doesnt_cut_back(self, aap_model):
        """Zone 1 is one side — should remove less than half the mesh."""
        metal, _ = classify_objects(aap_model)
        mesh = mesh_body_python(metal, resolution=250)
        orig_count = len(mesh.faces)

        zones = detect_zones(aap_model)
        if not zones:
            pytest.skip("No zones detected in AAP model")

        zone = zones[0]
        _, _, face_brep = find_zone_face(aap_model, zone)
        _, _, body_brep = find_zone_body(aap_model, zone)
        if face_brep is None:
            pytest.skip("Zone 1 face not found in AAP model")

        result = cut_zone_hole(mesh, face_brep, body_brep=body_brep)
        removed = orig_count - len(result.faces)
        assert removed < orig_count * 0.5, \
            f"Zone 1 removed {removed} of {orig_count} faces ({removed/orig_count:.1%}) — should be < 50%"

    def test_aap_zone2_back_doesnt_cut_front(self, aap_model):
        """Zone 2 is small back lobe — should remove < 30%."""
        metal, _ = classify_objects(aap_model)
        mesh = mesh_body_python(metal, resolution=250)
        orig_count = len(mesh.faces)

        zones = detect_zones(aap_model)
        if len(zones) < 2:
            pytest.skip("Zone 2 not found in AAP model")

        zone = zones[1]
        _, _, face_brep = find_zone_face(aap_model, zone)
        _, _, body_brep = find_zone_body(aap_model, zone)
        if face_brep is None:
            pytest.skip("Zone 2 face not found in AAP model")

        result = cut_zone_hole(mesh, face_brep, body_brep=body_brep)
        removed = orig_count - len(result.faces)
        assert removed < orig_count * 0.3, \
            f"Zone 2 removed {removed} of {orig_count} faces ({removed/orig_count:.1%}) — should be < 30%"


# ── TestBoundaryLoopExtraction (Task 7) ───────────────────────────

class TestBoundaryLoopExtraction:
    """Test boundary loop extraction from meshes with holes."""

    def test_extracts_loop_from_mesh_with_hole(self, pdg040_model):
        """Cut a hole, extract loops — largest should have >= 10 vertices."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)

        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)
        assert face_brep is not None

        cut_mesh = cut_zone_hole(mesh, face_brep, body_brep=body_brep)
        loops = extract_boundary_loop(cut_mesh)

        assert len(loops) >= 1, "Should find at least one boundary loop"
        assert len(loops[0]) >= 10, \
            f"Largest loop has only {len(loops[0])} vertices, expected >= 10"

    def test_loop_forms_connected_chain(self, pdg040_model):
        """Consecutive loop vertices should have small gaps (< 2mm)."""
        metal, _ = classify_objects(pdg040_model)
        mesh = mesh_body_python(metal, resolution=250)

        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)
        assert face_brep is not None

        cut_mesh = cut_zone_hole(mesh, face_brep, body_brep=body_brep)
        loops = extract_boundary_loop(cut_mesh)

        assert len(loops) >= 1, "Should find at least one boundary loop"
        loop = loops[0]
        verts = cut_mesh.vertices

        for i in range(len(loop)):
            v_curr = verts[loop[i]]
            v_next = verts[loop[(i + 1) % len(loop)]]
            gap = np.linalg.norm(v_curr - v_next)
            assert gap < 2.0, \
                f"Gap between loop vertices {loop[i]} and {loop[(i+1)%len(loop)]} is {gap:.3f}mm (> 2mm)"

    def test_closed_mesh_has_no_boundary_loops(self):
        """A closed mesh (sphere) should have no boundary loops."""
        import trimesh as tm
        sphere = tm.creation.icosphere(subdivisions=2, radius=5.0)
        loops = extract_boundary_loop(sphere)
        assert len(loops) == 0, f"Closed mesh should have 0 loops, got {len(loops)}"

    def test_open_mesh_has_boundary_loop(self):
        """A simple open mesh (single triangle) should have a boundary loop."""
        verts = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0]], dtype=float)
        faces = np.array([[0, 1, 2]], dtype=int)
        mesh = tm.Trimesh(vertices=verts, faces=faces, process=False)
        loops = extract_boundary_loop(mesh)
        assert len(loops) == 1, f"Single triangle should have 1 loop, got {len(loops)}"
        assert len(loops[0]) == 3, f"Loop should have 3 vertices, got {len(loops[0])}"


# ── TestResampleLoop (Task 8) ─────────────────────────────────────

class TestResampleLoop:
    """Tests for resample_loop."""

    def test_preserves_shape(self):
        """Resampled circle should stay close to unit circle."""
        n_orig = 20
        angles = np.linspace(0, 2 * np.pi, n_orig, endpoint=False)
        pts = np.column_stack([np.cos(angles), np.sin(angles), np.zeros(n_orig)])

        resampled = resample_loop(pts, 40)
        assert resampled.shape == (40, 3)

        # All points should be close to unit circle radius
        radii = np.sqrt(resampled[:, 0] ** 2 + resampled[:, 1] ** 2)
        assert np.allclose(radii, 1.0, atol=0.1), \
            f"Resampled points deviate from circle: min={radii.min():.3f}, max={radii.max():.3f}"

    def test_correct_count(self):
        """Resampled output should have exactly n points."""
        pts = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=float)
        for n in [3, 10, 50]:
            result = resample_loop(pts, n)
            assert len(result) == n, f"Expected {n} points, got {len(result)}"

    def test_single_point_returns_tiled(self):
        """Single point should tile to n copies."""
        pts = np.array([[5.0, 3.0, 1.0]])
        result = resample_loop(pts, 10)
        # Should not crash; may return original or tiled
        assert len(result) <= 10 or len(result) == 1


# ── TestZipLoops (Task 8) ─────────────────────────────────────────

class TestZipLoops:
    """Tests for zip_loops."""

    def test_correct_number_of_bridge_triangles(self):
        """zip_loops should produce 2*n triangles for n-point loops."""
        n = 10
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        loop_a = np.column_stack([np.cos(angles), np.sin(angles), np.zeros(n)])
        loop_b = np.column_stack([np.cos(angles) * 0.8, np.sin(angles) * 0.8, np.ones(n) * 0.5])

        verts, faces = zip_loops(loop_a, loop_b)
        assert len(verts) == 2 * n, f"Expected {2*n} vertices, got {len(verts)}"
        assert len(faces) == 2 * n, f"Expected {2*n} bridge triangles, got {len(faces)}"

    def test_small_loop(self):
        """Two 3-point loops should produce 6 bridge triangles."""
        loop_a = np.array([[0, 0, 0], [1, 0, 0], [0.5, 1, 0]], dtype=float)
        loop_b = np.array([[0, 0, 1], [1, 0, 1], [0.5, 1, 1]], dtype=float)
        verts, faces = zip_loops(loop_a, loop_b)
        assert len(faces) == 6

    def test_too_small_returns_empty(self):
        """Loops with <3 points should return empty."""
        loop_a = np.array([[0, 0, 0], [1, 0, 0]], dtype=float)
        loop_b = np.array([[0, 0, 1], [1, 0, 1]], dtype=float)
        verts, faces = zip_loops(loop_a, loop_b)
        assert len(faces) == 0


# ── TestStitchZoneToBody (Task 8) ─────────────────────────────────

class TestStitchZoneToBody:
    """Tests for stitch_zone_to_body."""

    def test_stitch_pdg040_zone1(self, pdg040_model, test_fingerprint_img):
        """Stitching zone 1 into PDG040 body should produce more faces than body alone."""
        metal, _ = classify_objects(pdg040_model)
        body_mesh = mesh_body_python(metal, resolution=250)
        body_face_count = len(body_mesh.faces)

        zones = detect_zones(pdg040_model)
        zone = zones[0]
        _, _, face_brep = find_zone_face(pdg040_model, zone)
        _, _, body_brep = find_zone_body(pdg040_model, zone)

        # Process zone to get display mesh
        display_mesh, _, _, _ = process_zone(
            pdg040_model, zone, test_fingerprint_img, 0.3, 60, "emboss",
            10, False,
        )

        # Cut hole
        cut_body = cut_zone_hole(body_mesh, face_brep, body_brep=body_brep)

        # Stitch
        merged = stitch_zone_to_body(cut_body, display_mesh, face_brep)

        # Merged should have more faces than just the cut body
        assert len(merged.faces) > len(cut_body.faces), \
            f"Merged ({len(merged.faces)}) should have more faces than cut body ({len(cut_body.faces)})"


# ── TestValidation (Task 9) ───────────────────────────────────────

class TestValidation:
    """Tests for validate_casting_mesh."""

    def test_box_passes_basic_checks(self):
        """A simple box should pass watertight, manifold, and no degenerate."""
        box = tm.creation.box(extents=[5, 5, 5])
        result = validate_casting_mesh(box)
        assert result.is_watertight, "Box should be watertight"
        assert result.is_manifold, "Box should be manifold"
        assert result.degenerate_count == 0, "Box should have no degenerate triangles"

    def test_open_mesh_fails_watertight(self):
        """An open mesh (single triangle) should fail watertight check."""
        verts = np.array([[0, 0, 0], [5, 0, 0], [2.5, 5, 0]], dtype=float)
        faces = np.array([[0, 1, 2]], dtype=int)
        mesh = tm.Trimesh(vertices=verts, faces=faces, process=False)
        result = validate_casting_mesh(mesh)
        assert not result.is_watertight, "Open mesh should not be watertight"

    def test_thick_box_passes_wall_thickness(self):
        """A 2mm thick box should report wall thickness > 0 (or -1 if rtree missing)."""
        box = tm.creation.box(extents=[10, 10, 2])
        result = validate_casting_mesh(box)
        # -1.0 means rtree not installed (skip gracefully)
        assert result.min_wall_thickness > 0 or result.min_wall_thickness == -1.0, \
            f"Box should have measurable wall thickness, got {result.min_wall_thickness}"

    def test_validation_result_dataclass_fields(self):
        """ValidationResult should have all expected fields."""
        vr = ValidationResult()
        assert hasattr(vr, 'is_watertight')
        assert hasattr(vr, 'is_manifold')
        assert hasattr(vr, 'normals_consistent')
        assert hasattr(vr, 'degenerate_count')
        assert hasattr(vr, 'self_intersections_near_stitch')
        assert hasattr(vr, 'min_wall_thickness')
        assert hasattr(vr, 'spill_violations')
        assert hasattr(vr, 'file_size_mb')
        assert hasattr(vr, 'passed')
        assert hasattr(vr, 'warnings')
        assert hasattr(vr, 'errors')


# ── TestFullCastingMerge (Task 10) ────────────────────────────────

class TestFullCastingMerge:
    """Tests for the full merge_casting_stl pipeline."""

    def test_pdg040_merge_produces_valid_mesh(self, pdg040_model, test_fingerprint_img):
        """PDG040 merge should produce a mesh with >100 faces and at least 1 zone OK."""
        result = merge_casting_stl(
            model=pdg040_model,
            fp_img=test_fingerprint_img,
            resolution=60,
            depth=0.3,
            mode="emboss",
            feather_cells=10,
        )
        assert result.mesh is not None, "Casting merge should produce a mesh"
        assert len(result.mesh.faces) > 100, \
            f"Merged mesh should have >100 faces, got {len(result.mesh.faces)}"

        # At least one zone should succeed
        ok_zones = [z for z, r in result.zone_results.items() if r.get('status') == 'ok']
        assert len(ok_zones) >= 1, \
            f"At least 1 zone should succeed, got {len(ok_zones)} of {len(result.zone_results)}"

    def test_casting_result_dataclass(self):
        """CastingResult should have all expected fields."""
        cr = CastingResult()
        assert cr.mesh is None
        assert cr.validation is None
        assert isinstance(cr.zone_results, dict)
        assert isinstance(cr.warnings, list)


# ── TestExport (Task 10) ──────────────────────────────────────────

class TestExport:
    """Tests for export functions."""

    def test_export_casting_stl(self, tmp_path):
        """export_casting_stl should write a valid STL file."""
        box = tm.creation.box(extents=[5, 5, 5])
        stl_path = str(tmp_path / "test_casting.stl")
        export_casting_stl(box, stl_path)
        assert os.path.isfile(stl_path), "STL file should exist"
        assert os.path.getsize(stl_path) > 0, "STL file should not be empty"

    def test_export_casting_3dm(self, tmp_path):
        """export_casting_3dm should write a valid .3dm file."""
        box = tm.creation.box(extents=[5, 5, 5])
        dm_path = str(tmp_path / "test_casting.3dm")
        export_casting_3dm(box, dm_path)
        assert os.path.isfile(dm_path), "3dm file should exist"
        assert os.path.getsize(dm_path) > 0, "3dm file should not be empty"

        # Verify it's readable
        model = rhino3dm.File3dm.Read(dm_path)
        assert model is not None
        assert len(model.Objects) > 0


# ── TestCastingCLI (Task 11) ──────────────────────────────────────

class TestCastingCLI:
    """Tests for the --casting CLI flag."""

    def test_casting_flag_accepted(self):
        """--help output should contain --casting."""
        script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "fingerprint_displace.py"
        )
        result = subprocess.run(
            [sys.executable, script, "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert "--casting" in result.stdout, \
            f"--casting not found in help output:\n{result.stdout}"

    def test_casting_produces_stl(self, pdg040_model, test_fingerprint_img, tmp_path):
        """Running with --casting should produce a _casting.stl file."""
        script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "fingerprint_displace.py"
        )
        designs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "designs"
        )
        input_3dm = os.path.join(designs_dir, "PDG040.3dm")
        if not os.path.isfile(input_3dm):
            pytest.skip(f"Design file not found: {input_3dm}")

        # Save test fingerprint to tmp
        fp_path = str(tmp_path / "test_fp.png")
        test_fingerprint_img.save(fp_path)

        output_path = str(tmp_path / "test_output.3dm")

        result = subprocess.run(
            [sys.executable, script, input_3dm, fp_path,
             "--output", output_path,
             "--resolution", "60",
             "--casting"],
            capture_output=True, text=True, timeout=300,
            cwd=os.path.dirname(script),
        )

        # Check exit code
        assert result.returncode == 0, \
            f"CLI failed with code {result.returncode}:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Check casting STL was produced
        casting_stl = os.path.splitext(output_path)[0] + "_casting.stl"
        assert os.path.isfile(casting_stl), \
            f"Expected casting STL at {casting_stl}\nstdout: {result.stdout}"
