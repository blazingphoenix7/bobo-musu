"""
Stress / edge-case tests for the fingerprint preview pipeline.

These tests exercise boundary conditions: tiny images, uniform images,
extreme depth values, all zones, and rapid sequential requests.
Every test uses ``resolution=80`` for speed.
"""

import hashlib
import io

import numpy as np
import pytest
from PIL import Image

from preview.pipeline import generate_preview_stl, PipelineError
from preview.design_registry import get_design_path, _cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_design_cache():
    """Clear the design registry cache before every test."""
    _cache.clear()
    yield
    _cache.clear()


def _save_grayscale(array: np.ndarray, path) -> str:
    """Save a numpy uint8 array as a grayscale PNG and return the path string."""
    img = Image.fromarray(array.astype(np.uint8), mode="L")
    img.save(str(path))
    return str(path)


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.timeout(120)
class TestAllZonesMaxDesign:
    """Run all 5 zones on the highest-density design to verify completeness."""

    def test_all_zones_max_design_completes(self, synthetic_fingerprint):
        """PDG040, zones 1-5, resolution=80 – every zone must return valid
        non-empty STL bytes."""
        for zone in range(1, 6):
            print(f"Generating zone {zone}/5 ...")
            result = generate_preview_stl(
                design_path=get_design_path("PDG040"),
                fingerprint_file=synthetic_fingerprint,
                zones=[zone],
                mode="emboss",
                resolution=80,
            )
            stl_bytes = result[zone]
            print(
                f"  Zone {zone}: {len(stl_bytes)} bytes, MD5={_md5(stl_bytes)}"
            )
            assert isinstance(stl_bytes, bytes), f"Zone {zone} did not return bytes"
            assert len(stl_bytes) > 0, f"Zone {zone} returned empty bytes"


@pytest.mark.timeout(120)
class TestEdgeCaseImages:
    """Images at the extremes of size and content."""

    def test_1px_fingerprint_doesnt_crash(self, tmp_path):
        """A 1x1 pixel fingerprint must not crash – it should either return
        valid output or raise a clean PipelineError."""
        one_px = _save_grayscale(np.array([[128]], dtype=np.uint8), tmp_path / "1px.png")
        print(f"Created 1x1 image at {one_px}")

        try:
            result = generate_preview_stl(
                design_path=get_design_path("PDG040"),
                fingerprint_file=one_px,
                zones=[1],
                mode="emboss",
                resolution=80,
            )
            stl_bytes = result[1]
            print(f"Returned {len(stl_bytes)} bytes (no error)")
            assert isinstance(stl_bytes, bytes)
        except PipelineError as exc:
            print(f"PipelineError (acceptable): {exc}")
        except Exception as exc:
            pytest.fail(f"Unexpected exception for 1x1 image: {type(exc).__name__}: {exc}")

    def test_pure_white_fingerprint(self, tmp_path):
        """An all-white (255) fingerprint must produce valid output."""
        white = _save_grayscale(
            np.full((300, 300), 255, dtype=np.uint8), tmp_path / "white.png"
        )
        print(f"Created all-white image at {white}")

        result = generate_preview_stl(
            design_path=get_design_path("PDG040"),
            fingerprint_file=white,
            zones=[1],
            mode="emboss",
            resolution=80,
        )
        stl_bytes = result[1]
        print(f"Pure-white result: {len(stl_bytes)} bytes, MD5={_md5(stl_bytes)}")
        assert isinstance(stl_bytes, bytes) and len(stl_bytes) > 0

    def test_pure_black_fingerprint(self, tmp_path):
        """An all-black (0) fingerprint must produce valid output."""
        black = _save_grayscale(
            np.zeros((300, 300), dtype=np.uint8), tmp_path / "black.png"
        )
        print(f"Created all-black image at {black}")

        result = generate_preview_stl(
            design_path=get_design_path("PDG040"),
            fingerprint_file=black,
            zones=[1],
            mode="emboss",
            resolution=80,
        )
        stl_bytes = result[1]
        print(f"Pure-black result: {len(stl_bytes)} bytes, MD5={_md5(stl_bytes)}")
        assert isinstance(stl_bytes, bytes) and len(stl_bytes) > 0


@pytest.mark.timeout(120)
class TestExtremeDepthValues:
    """Very small and very large depth parameters."""

    def test_very_small_depth(self, synthetic_fingerprint):
        """depth=0.01 mm must still produce valid output."""
        print("Generating with depth=0.01 ...")
        result = generate_preview_stl(
            design_path=get_design_path("PDG040"),
            fingerprint_file=synthetic_fingerprint,
            zones=[1],
            mode="emboss",
            resolution=80,
            depth=0.01,
        )
        stl_bytes = result[1]
        print(f"Small-depth result: {len(stl_bytes)} bytes, MD5={_md5(stl_bytes)}")
        assert isinstance(stl_bytes, bytes) and len(stl_bytes) > 0

    def test_very_large_depth(self, synthetic_fingerprint):
        """depth=2.0 mm must produce valid output (may be clamped internally)."""
        print("Generating with depth=2.0 ...")
        result = generate_preview_stl(
            design_path=get_design_path("PDG040"),
            fingerprint_file=synthetic_fingerprint,
            zones=[1],
            mode="emboss",
            resolution=80,
            depth=2.0,
        )
        stl_bytes = result[1]
        print(f"Large-depth result: {len(stl_bytes)} bytes, MD5={_md5(stl_bytes)}")
        assert isinstance(stl_bytes, bytes) and len(stl_bytes) > 0


@pytest.mark.timeout(120)
class TestRapidSequentialRequests:
    """Fire several requests in quick succession (serially)."""

    def test_rapid_sequential_requests(self, synthetic_fingerprint):
        """5 sequential calls must all succeed and return non-empty bytes."""
        results = []
        for i in range(5):
            print(f"Sequential request {i + 1}/5 ...")
            result = generate_preview_stl(
                design_path=get_design_path("PDG040"),
                fingerprint_file=synthetic_fingerprint,
                zones=[1],
                mode="emboss",
                resolution=80,
            )
            stl_bytes = result[1]
            results.append(stl_bytes)
            print(
                f"  Request {i + 1}: {len(stl_bytes)} bytes, MD5={_md5(stl_bytes)}"
            )

        for idx, r in enumerate(results, start=1):
            assert isinstance(r, bytes) and len(r) > 0, (
                f"Request {idx} returned invalid output"
            )
        print(f"\nAll 5 sequential requests succeeded.")
