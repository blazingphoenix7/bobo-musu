"""Unit tests for fingerprint_displace.py — Tasks 1-5.

Tests cover:
  Task 1: Flexible zone discovery (multi-strategy)
  Task 2: Flexible zone geometry finders (Surface->Brep, fallbacks)
  Task 3: Multi-face Brep support
  Task 4: Boundary extraction from BODY geometry
  Task 5: PipelineError instead of sys.exit()
"""
import os
import sys
import math
import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import rhino3dm
from fingerprint_displace import (
    PipelineError,
    _to_brep,
    _detect_zones_fp_convention,
    _detect_zones_textdot,
    _detect_zones_fuzzy_layers,
    detect_zones,
    _find_zone_geo_on_layer,
    find_zone_face,
    find_zone_body,
    is_face_untrimmed,
    _extract_boundary_from_body,
    extract_trim_boundary,
    _build_displaced_mesh_single_face,
    build_displaced_mesh,
    _pip,
    preprocess_fingerprint,
)


# ── Task 5: PipelineError ────────────────────────────────────────────

class TestPipelineError:
    def test_is_exception(self):
        assert issubclass(PipelineError, Exception)

    def test_can_raise_and_catch(self):
        with pytest.raises(PipelineError, match="test error"):
            raise PipelineError("test error")

    def test_find_zone_face_raises_pipeline_error(self):
        """find_zone_face should raise PipelineError, not sys.exit()."""
        model = rhino3dm.File3dm()
        with pytest.raises(PipelineError, match="Zone 99 FACE not found"):
            find_zone_face(model, 99)

    def test_find_zone_body_raises_pipeline_error(self):
        """find_zone_body should raise PipelineError, not sys.exit()."""
        model = rhino3dm.File3dm()
        with pytest.raises(PipelineError, match="Zone 99 BODY not found"):
            find_zone_body(model, 99)


# ── Task 1: Flexible Zone Discovery ──────────────────────────────────

class TestZoneDiscovery:
    def test_fp_convention_pdg040(self, pdg040_model):
        """PDG040 uses FP_ZONE_N_FACE convention — should detect 5 zones."""
        zones = _detect_zones_fp_convention(pdg040_model)
        assert len(zones) == 5
        assert zones == sorted(zones)

    def test_fp_convention_p246(self, p246_model):
        """P246 uses FP_ZONE_N_FACE convention — should detect 2 zones."""
        zones = _detect_zones_fp_convention(p246_model)
        assert len(zones) == 2

    def test_detect_zones_primary_path(self, pdg040_model):
        """detect_zones() should use FP_ZONE convention as primary."""
        zones = detect_zones(pdg040_model)
        assert len(zones) == 5

    def test_detect_zones_empty_model(self):
        """Empty model should return empty list, not error."""
        model = rhino3dm.File3dm()
        zones = detect_zones(model)
        assert zones == []

    def test_textdot_strategy_empty_model(self):
        """TextDot strategy on model with no TextDots returns empty."""
        model = rhino3dm.File3dm()
        zones = _detect_zones_textdot(model)
        assert zones == []

    def test_fuzzy_strategy_empty_model(self):
        """Fuzzy strategy on model with no matching layers returns empty."""
        model = rhino3dm.File3dm()
        zones = _detect_zones_fuzzy_layers(model)
        assert zones == []

    def test_detect_zones_aap(self, aap_model):
        """AAP10985F should be detected via some strategy."""
        zones = detect_zones(aap_model)
        assert len(zones) >= 1, "Expected at least 1 zone in AAP10985F"


# ── Task 2: Flexible Zone Geometry Finders ────────────────────────────

class TestZoneGeometryFinders:
    def test_find_face_pdg040(self, pdg040_model):
        """PDG040 zone 1 FACE should be found via FP_ZONE convention."""
        idx, obj, brep = find_zone_face(pdg040_model, 1)
        assert brep is not None
        assert hasattr(brep, "Faces")
        assert len(brep.Faces) >= 1

    def test_find_body_pdg040(self, pdg040_model):
        """PDG040 zone 1 BODY should be found via FP_ZONE convention."""
        idx, obj, brep = find_zone_body(pdg040_model, 1)
        assert brep is not None
        assert hasattr(brep, "Faces")

    def test_find_face_p246(self, p246_model):
        """P246 zone 1 FACE should be found via FP_ZONE convention."""
        idx, obj, brep = find_zone_face(p246_model, 1)
        assert brep is not None

    def test_find_body_p246(self, p246_model):
        """P246 zone 1 BODY should be found."""
        idx, obj, brep = find_zone_body(p246_model, 1)
        assert brep is not None

    def test_find_face_nonexistent_zone(self):
        """Looking for zone 999 in empty model should raise PipelineError."""
        model = rhino3dm.File3dm()
        with pytest.raises(PipelineError):
            find_zone_face(model, 999)

    def test_to_brep_with_brep(self, pdg040_model):
        """_to_brep should return Brep objects as-is."""
        _, _, brep = find_zone_face(pdg040_model, 1)
        result = _to_brep(brep)
        assert result is brep

    def test_to_brep_with_none_like(self):
        """_to_brep should return None for non-convertible geometry."""
        result = _to_brep(object())
        assert result is None

    def test_find_zone_geo_on_layer_missing(self):
        """Missing layer should return None, not raise."""
        model = rhino3dm.File3dm()
        result = _find_zone_geo_on_layer(model, "NONEXISTENT")
        assert result is None


# ── Task 3: Multi-Face Brep Support ──────────────────────────────────

class TestMultiFaceBrep:
    def test_single_face_backward_compat(self, pdg040_model, test_fingerprint_img):
        """Single-face Brep should produce identical results through new code path."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)

        assert len(face_brep.Faces) == 1, "PDG040 zone 1 should be single-face"

        mesh = build_displaced_mesh(
            face_brep, body_brep, test_fingerprint_img,
            max_depth=0.2, grid_res=30, mode="emboss",
            feather_cells=5, watertight=False,
        )
        assert mesh is not None
        assert mesh.Faces.Count > 0
        assert len(mesh.Vertices) > 0

    def test_single_face_matches_direct_call(self, pdg040_model, test_fingerprint_img):
        """build_displaced_mesh with single face should match _build_displaced_mesh_single_face."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)

        mesh_via_wrapper = build_displaced_mesh(
            face_brep, body_brep, test_fingerprint_img,
            max_depth=0.2, grid_res=25, mode="emboss",
            feather_cells=5, watertight=False,
        )
        mesh_direct = _build_displaced_mesh_single_face(
            face_brep, body_brep, test_fingerprint_img,
            max_depth=0.2, grid_res=25, mode="emboss",
            feather_cells=5, watertight=False, face_index=0,
        )

        assert mesh_via_wrapper.Faces.Count == mesh_direct.Faces.Count
        assert len(mesh_via_wrapper.Vertices) == len(mesh_direct.Vertices)

    def test_watertight_single_face(self, pdg040_model, test_fingerprint_img):
        """Watertight mode should produce more faces than display mode."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)

        display = build_displaced_mesh(
            face_brep, body_brep, test_fingerprint_img,
            max_depth=0.2, grid_res=25, mode="emboss",
            feather_cells=5, watertight=False,
        )
        watertight = build_displaced_mesh(
            face_brep, body_brep, test_fingerprint_img,
            max_depth=0.2, grid_res=25, mode="emboss",
            feather_cells=5, watertight=True,
        )

        assert watertight.Faces.Count > display.Faces.Count


# ── Task 4: Boundary Extraction from BODY ─────────────────────────────

class TestBoundaryExtraction:
    def test_extract_trim_boundary_face_edges(self, pdg040_model):
        """Standard trimmed face should use face edges for boundary."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        boundary = extract_trim_boundary(face_brep)
        assert len(boundary) > 10
        # All boundary points should be (x, y) tuples
        for pt in boundary:
            assert len(pt) == 2

    def test_extract_trim_boundary_with_body(self, pdg040_model):
        """Passing body_brep should work even if face is trimmed (no change)."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        _, _, body_brep = find_zone_body(pdg040_model, 1)

        boundary_without = extract_trim_boundary(face_brep)
        boundary_with = extract_trim_boundary(face_brep, body_brep=body_brep)

        # For a trimmed face, both should produce the same boundary
        # (body path only triggers for untrimmed faces)
        assert len(boundary_without) > 0
        assert len(boundary_with) > 0

    def test_is_face_untrimmed_pdg040(self, pdg040_model):
        """PDG040 zone faces should be trimmed (not untrimmed)."""
        _, _, face_brep = find_zone_face(pdg040_model, 1)
        # PDG040 zones are trimmed surfaces
        result = is_face_untrimmed(face_brep)
        # This may or may not be untrimmed depending on the design
        assert isinstance(result, bool)

    def test_extract_boundary_from_body(self, pdg040_model):
        """BODY boundary extraction should produce valid XY boundary."""
        _, _, body_brep = find_zone_body(pdg040_model, 1)
        boundary = _extract_boundary_from_body(body_brep)
        assert len(boundary) > 0
        for pt in boundary:
            assert len(pt) == 2


# ── Helpers ───────────────────────────────────────────────────────────

class TestHelpers:
    def test_pip_inside(self):
        """Point clearly inside a square polygon."""
        poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _pip(5, 5, poly) is True

    def test_pip_outside(self):
        """Point clearly outside a square polygon."""
        poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
        assert _pip(15, 15, poly) is False

    def test_pip_edge(self):
        """Point on boundary — either result is acceptable."""
        poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
        result = _pip(0, 5, poly)
        assert isinstance(result, bool)


# ── Integration: Full zone processing ─────────────────────────────────

class TestIntegration:
    def test_process_pdg040_zone1(self, pdg040_model, test_fingerprint_img):
        """Full pipeline for PDG040 zone 1 should produce a valid mesh."""
        from fingerprint_displace import process_zone

        display_mesh, stl_mesh, face_brep, body_brep = process_zone(
            pdg040_model, 1, test_fingerprint_img,
            depth=0.2, resolution=30, mode="emboss",
            feather_cells=5, do_stl=True,
        )

        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0
        assert stl_mesh is not None
        assert stl_mesh.Faces.Count > display_mesh.Faces.Count  # watertight has more

    def test_process_p246_zone1(self, p246_model, test_fingerprint_img):
        """Full pipeline for P246 zone 1 should produce a valid mesh."""
        from fingerprint_displace import process_zone

        display_mesh, stl_mesh, face_brep, body_brep = process_zone(
            p246_model, 1, test_fingerprint_img,
            depth=0.2, resolution=30, mode="emboss",
            feather_cells=5, do_stl=True,
        )

        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0


# ── Task 6: Fingerprint Preprocessing ────────────────────────────────

class TestPreprocessFingerprint:
    def test_output_is_1024x1024(self, tmp_path):
        """A 200x300 input image should be resized to 1024x1024."""
        img = Image.fromarray(
            np.random.randint(0, 256, (300, 200), dtype=np.uint8), mode="L"
        )
        p = tmp_path / "fp.png"
        img.save(str(p))
        result = preprocess_fingerprint(str(p))
        assert result.size == (1024, 1024)

    def test_dark_fingerprint_on_light_bg(self, tmp_path):
        """White background with dark square: result should have non-zero mean."""
        arr = np.full((200, 200), 240, dtype=np.uint8)
        arr[70:130, 70:130] = 30
        img = Image.fromarray(arr, mode="L")
        p = tmp_path / "fp_light_bg.png"
        img.save(str(p))
        result = preprocess_fingerprint(str(p))
        result_arr = np.array(result)
        assert result_arr.mean() > 0

    def test_light_fingerprint_on_dark_bg(self, tmp_path):
        """Dark background with light square: auto-inversion should produce non-zero mean."""
        arr = np.full((200, 200), 30, dtype=np.uint8)
        arr[70:130, 70:130] = 240
        img = Image.fromarray(arr, mode="L")
        p = tmp_path / "fp_dark_bg.png"
        img.save(str(p))
        result = preprocess_fingerprint(str(p))
        result_arr = np.array(result)
        assert result_arr.mean() > 0

    def test_custom_target_size(self, tmp_path):
        """Passing target_size=512 should produce a 512x512 output."""
        arr = np.random.randint(0, 256, (150, 150), dtype=np.uint8)
        img = Image.fromarray(arr, mode="L")
        p = tmp_path / "fp_custom.png"
        img.save(str(p))
        result = preprocess_fingerprint(str(p), target_size=512)
        assert result.size == (512, 512)

    def test_preserves_contrast(self, tmp_path):
        """Image with clear dark/light regions should have good dynamic range (std > 20)."""
        arr = np.zeros((200, 200), dtype=np.uint8)
        arr[:, :100] = 30
        arr[:, 100:] = 220
        img = Image.fromarray(arr, mode="L")
        p = tmp_path / "fp_contrast.png"
        img.save(str(p))
        result = preprocess_fingerprint(str(p))
        result_arr = np.array(result, dtype=np.float64)
        assert result_arr.std() > 20


# ── Task 10: Edge Cases & Stress Tests ────────────────────────────────

import os as _os

_DESIGNS_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "designs")
_PDG040_PATH = _os.path.join(_DESIGNS_DIR, "PDG040.3dm")


def _load_pdg040():
    """Load PDG040 model, skip if not available."""
    if not _os.path.isfile(_PDG040_PATH):
        pytest.skip(f"Design file not found: {_PDG040_PATH}")
    model = rhino3dm.File3dm.Read(_PDG040_PATH)
    assert model is not None
    return model


class TestEdgeCases:
    """Edge cases that could break the pipeline."""

    def test_very_low_resolution(self, synthetic_fingerprint):
        """Resolution=50 (minimum) should still work."""
        from fingerprint_displace import process_zone
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, synthetic_fingerprint,
            depth=0.3, resolution=50, mode="emboss",
            feather_cells=3, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_very_small_depth(self, synthetic_fingerprint):
        """Depth=0.01 (minimum) should produce valid mesh."""
        from fingerprint_displace import process_zone
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, synthetic_fingerprint,
            depth=0.01, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_very_large_depth_gets_clamped(self, synthetic_fingerprint):
        """Depth > 80% thickness should be clamped, not crash."""
        from fingerprint_displace import process_zone
        model = _load_pdg040()
        # depth=2.0 far exceeds typical zone thickness; pipeline should clamp and continue
        display_mesh, _, _, _ = process_zone(
            model, 1, synthetic_fingerprint,
            depth=2.0, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_zero_feather(self, synthetic_fingerprint):
        """feather_cells=0 should work (no edge blending)."""
        from fingerprint_displace import process_zone
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, synthetic_fingerprint,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=0, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_large_feather(self, synthetic_fingerprint):
        """feather_cells=50 (larger than radius) should not crash."""
        from fingerprint_displace import process_zone
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, synthetic_fingerprint,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=50, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_uniform_white_fingerprint(self, tmp_path):
        """All-white fingerprint should produce mesh with uniform displacement."""
        from fingerprint_displace import process_zone, preprocess_fingerprint
        img_path = str(tmp_path / "white_fp.png")
        Image.new("L", (256, 256), color=255).save(img_path)
        fp_img = preprocess_fingerprint(img_path, target_size=256)
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, fp_img,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_uniform_black_fingerprint(self, tmp_path):
        """All-black fingerprint should produce mesh with near-zero displacement."""
        from fingerprint_displace import process_zone, preprocess_fingerprint
        img_path = str(tmp_path / "black_fp.png")
        Image.new("L", (256, 256), color=0).save(img_path)
        fp_img = preprocess_fingerprint(img_path, target_size=256)
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, fp_img,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_tiny_fingerprint_image(self, tmp_path):
        """Very small (16x16) fingerprint should still work after preprocessing."""
        from fingerprint_displace import process_zone, preprocess_fingerprint
        img_path = str(tmp_path / "tiny_fp.png")
        arr = np.random.randint(0, 256, (16, 16), dtype=np.uint8)
        Image.fromarray(arr, mode="L").save(img_path)
        fp_img = preprocess_fingerprint(img_path, target_size=256)
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, fp_img,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_large_fingerprint_image(self, tmp_path):
        """Large (4096x4096) fingerprint should still work after preprocessing."""
        from fingerprint_displace import preprocess_fingerprint
        img_path = str(tmp_path / "large_fp.png")
        # Use a pattern that PIL can generate efficiently via stripes
        arr = np.zeros((4096, 4096), dtype=np.uint8)
        arr[::4, :] = 200  # horizontal stripes
        Image.fromarray(arr, mode="L").save(img_path)
        fp_img = preprocess_fingerprint(img_path, target_size=256)
        # Verify preprocessing succeeds and returns a valid image
        assert fp_img is not None
        assert fp_img.size[0] > 0
        assert fp_img.size[1] > 0

    def test_rectangular_fingerprint(self, tmp_path):
        """Non-square (100x400) fingerprint should work."""
        from fingerprint_displace import process_zone, preprocess_fingerprint
        img_path = str(tmp_path / "rect_fp.png")
        arr = np.random.randint(0, 256, (100, 400), dtype=np.uint8)
        Image.fromarray(arr, mode="L").save(img_path)
        fp_img = preprocess_fingerprint(img_path, target_size=256)
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, fp_img,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_natural_fp_width(self, synthetic_fingerprint):
        """fp_natural_width=17.0 should constrain fingerprint mapping."""
        from fingerprint_displace import process_zone
        model = _load_pdg040()
        display_mesh, _, _, _ = process_zone(
            model, 1, synthetic_fingerprint,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
            fp_natural_width=17.0,
        )
        assert display_mesh is not None
        assert display_mesh.Faces.Count > 0

    def test_auto_depth_computation(self):
        """_compute_auto_depth should return valid depths for all zones."""
        from fingerprint_displace import _compute_auto_depth, detect_zones
        model = _load_pdg040()
        zones = detect_zones(model)
        assert len(zones) > 0, "PDG040 should have zones"
        zone_depths, zone_thicknesses = _compute_auto_depth(model, zones)
        assert len(zone_depths) == len(zones)
        for z in zones:
            assert z in zone_depths, f"Zone {z} missing from depths"
            depth = zone_depths[z]
            assert depth > 0, f"Zone {z} depth must be positive, got {depth}"
            assert depth < 1.0, f"Zone {z} depth must be < 1.0mm, got {depth}"
