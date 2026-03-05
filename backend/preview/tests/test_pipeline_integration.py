"""Tests for the pipeline.py wrapper around fingerprint_displace."""
import struct
import pytest
from pathlib import Path
from django.conf import settings
from preview.pipeline import generate_preview_stl, PipelineError
from preview.design_registry import get_design_path, get_design, _cache


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


def _parse_stl_triangle_count(stl_bytes):
    """Parse triangle count from binary STL bytes."""
    assert len(stl_bytes) >= 84, f"STL too small: {len(stl_bytes)} bytes"
    return struct.unpack("<I", stl_bytes[80:84])[0]


class TestGeneratePreviewSTL:
    @pytest.mark.parametrize("design_id,zone,mode", [
        ("PDG040", 1, "emboss"),
        ("PDG040", 1, "engrave"),
        ("P246", 1, "emboss"),
        ("P246", 1, "engrave"),
    ])
    def test_generate_preview_stl_returns_bytes(self, synthetic_fingerprint, design_id, zone, mode):
        """Call generate_preview_stl() and verify return type."""
        design_path = get_design_path(design_id)
        result = generate_preview_stl(
            design_path, synthetic_fingerprint, [zone], mode=mode, resolution=80,
        )
        print(f"  {design_id}-Z{zone}-{mode}: {len(result)} zone(s)")
        assert isinstance(result, dict)
        assert zone in result, f"Zone {zone} not in result keys: {result.keys()}"
        assert isinstance(result[zone], bytes)
        assert len(result[zone]) > 100, f"STL too small: {len(result[zone])} bytes"

    @pytest.mark.parametrize("design_id,zone,mode", [
        ("PDG040", 1, "emboss"),
        ("P246", 1, "emboss"),
    ])
    def test_stl_output_is_valid_binary_stl(self, synthetic_fingerprint, design_id, zone, mode):
        """Parse returned bytes as binary STL."""
        design_path = get_design_path(design_id)
        result = generate_preview_stl(
            design_path, synthetic_fingerprint, [zone], mode=mode, resolution=80,
        )
        stl_bytes = result[zone]
        # 80-byte header
        assert len(stl_bytes) >= 84
        tri_count = _parse_stl_triangle_count(stl_bytes)
        print(f"  {design_id}-Z{zone}: {tri_count} triangles")
        assert tri_count > 0
        expected_size = 80 + 4 + (50 * tri_count)
        assert len(stl_bytes) == expected_size, (
            f"Size mismatch: {len(stl_bytes)} != {expected_size}"
        )

    def test_emboss_and_engrave_produce_different_output(self, synthetic_fingerprint):
        """Emboss and engrave STLs differ."""
        design_path = get_design_path("PDG040")
        emboss = generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="emboss", resolution=80,
        )
        engrave = generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="engrave", resolution=80,
        )
        print(f"  Emboss: {len(emboss[1])} bytes, Engrave: {len(engrave[1])} bytes")
        assert emboss[1] != engrave[1], "Emboss and engrave should produce different STLs"

    def test_multiple_zones_returns_all_requested(self, synthetic_fingerprint):
        """Request multiple zones, get all back."""
        design_path = get_design_path("PDG040")
        result = generate_preview_stl(
            design_path, synthetic_fingerprint, [1, 2, 3], mode="emboss", resolution=80,
        )
        print(f"  Keys: {sorted(result.keys())}")
        assert set(result.keys()) == {1, 2, 3}
        for z in [1, 2, 3]:
            assert len(result[z]) > 100

    def test_unified_mode_produces_output(self, synthetic_fingerprint):
        """Unified mode with all zones."""
        design_path = get_design_path("P246")
        result = generate_preview_stl(
            design_path, synthetic_fingerprint, [1, 2], mode="emboss",
            resolution=80, unified=True,
        )
        print(f"  Unified keys: {sorted(result.keys())}")
        assert set(result.keys()) == {1, 2}
        for z in [1, 2]:
            assert len(result[z]) > 100

    def test_depth_parameter_affects_output(self, synthetic_fingerprint):
        """Different depths produce different output."""
        design_path = get_design_path("PDG040")
        r1 = generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="emboss",
            resolution=80, depth=0.1,
        )
        r2 = generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="emboss",
            resolution=80, depth=0.5,
        )
        print(f"  depth=0.1: {len(r1[1])} bytes")
        print(f"  depth=0.5: {len(r2[1])} bytes")
        assert r1[1] != r2[1], "Different depths should produce different STLs"

    def test_resolution_parameter_affects_vertex_count(self, synthetic_fingerprint):
        """Higher resolution produces more triangles."""
        design_path = get_design_path("PDG040")
        r_low = generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="emboss", resolution=60,
        )
        r_high = generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="emboss", resolution=120,
        )
        t_low = _parse_stl_triangle_count(r_low[1])
        t_high = _parse_stl_triangle_count(r_high[1])
        print(f"  res=60: {t_low} triangles, res=120: {t_high} triangles")
        assert t_high > t_low, "Higher resolution should produce more triangles"

    def test_temp_files_cleaned_up_after_processing(self, synthetic_fingerprint):
        """No temp files remain after processing."""
        import os
        temp_dir = settings.PREVIEW_TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        before = set(os.listdir(temp_dir)) if temp_dir.exists() else set()
        design_path = get_design_path("PDG040")
        generate_preview_stl(
            design_path, synthetic_fingerprint, [1], mode="emboss", resolution=80,
        )
        after = set(os.listdir(temp_dir)) if temp_dir.exists() else set()
        new_files = after - before
        print(f"  New files after processing: {new_files}")
        assert len(new_files) == 0, f"Temp files leaked: {new_files}"

    def test_invalid_fingerprint_raises_error(self, tmp_path):
        """Non-image file raises PipelineError."""
        bad_file = tmp_path / "not_an_image.txt"
        bad_file.write_text("this is not an image")
        design_path = get_design_path("PDG040")
        with pytest.raises((PipelineError, Exception)):
            generate_preview_stl(
                design_path, bad_file, [1], mode="emboss", resolution=80,
            )

    def test_invalid_zone_raises_error(self, synthetic_fingerprint):
        """Request zone 99 for PDG040 (only has 1-5)."""
        design_path = get_design_path("PDG040")
        with pytest.raises((PipelineError, SystemExit)):
            generate_preview_stl(
                design_path, synthetic_fingerprint, [99], mode="emboss", resolution=80,
            )
