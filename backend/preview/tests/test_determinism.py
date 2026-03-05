"""
Test determinism of the fingerprint preview STL generation pipeline.

Ensures that identical inputs always produce byte-identical STL output,
and that varying any single parameter produces different output.
"""

import hashlib

import pytest

from preview.pipeline import generate_preview_stl, PipelineError
from preview.design_registry import get_design_path, _cache


@pytest.fixture(autouse=True)
def clear_design_cache():
    """Clear the design registry cache before every test."""
    _cache.clear()
    yield
    _cache.clear()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _md5(data: bytes) -> str:
    """Return the hex MD5 digest of *data*."""
    return hashlib.md5(data).hexdigest()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDeterminism:
    """Identical inputs must always yield byte-identical STL output."""

    def test_same_request_produces_identical_stl_bytes(self, synthetic_fingerprint):
        """Two back-to-back calls with the same parameters must return
        identical bytes (verified via MD5)."""
        params = dict(
            design_path=get_design_path("PDG040"),
            fingerprint_file=synthetic_fingerprint,
            zones=[1],
            mode="emboss",
            resolution=80,
        )

        result_a = generate_preview_stl(**params)
        result_b = generate_preview_stl(**params)

        stl_a = result_a[1]
        stl_b = result_b[1]

        digest_a = _md5(stl_a)
        digest_b = _md5(stl_b)

        print(f"Run A  MD5: {digest_a}")
        print(f"Run B  MD5: {digest_b}")
        print(f"Byte lengths: A={len(stl_a)}, B={len(stl_b)}")

        assert digest_a == digest_b, (
            f"Expected identical output but got different MD5 digests: "
            f"{digest_a} vs {digest_b}"
        )

    def test_determinism_across_ten_runs(self, synthetic_fingerprint):
        """Run the same request 10 times and assert every MD5 is identical."""
        params = dict(
            design_path=get_design_path("PDG040"),
            fingerprint_file=synthetic_fingerprint,
            zones=[1],
            mode="emboss",
            resolution=80,
        )

        digests = []
        for i in range(10):
            result = generate_preview_stl(**params)
            stl_bytes = result[1]
            digest = _md5(stl_bytes)
            digests.append(digest)
            print(f"Run {i + 1:>2}/10  MD5: {digest}  size: {len(stl_bytes)} bytes")

        unique = set(digests)
        print(f"\nUnique digests: {len(unique)}")
        assert len(unique) == 1, (
            f"Expected 1 unique digest across 10 runs but got {len(unique)}: {unique}"
        )


class TestDifferentInputsProduceDifferentOutput:
    """Varying a single parameter must change the output."""

    def test_different_fingerprint_produces_different_output(
        self, synthetic_fingerprint, tmp_path
    ):
        """Two distinct fingerprint images must produce different STL bytes."""
        import numpy as np
        from PIL import Image

        # Create a second, visually different fingerprint image.
        alt_array = np.random.default_rng(seed=9999).integers(
            0, 256, (300, 300), dtype=np.uint8
        )
        alt_path = tmp_path / "alt_fingerprint.png"
        Image.fromarray(alt_array, mode="L").save(str(alt_path))

        common = dict(design_path=get_design_path("PDG040"), zones=[1], mode="emboss", resolution=80)

        result_a = generate_preview_stl(fingerprint_file=synthetic_fingerprint, **common)
        result_b = generate_preview_stl(fingerprint_file=str(alt_path), **common)

        stl_a = result_a[1]
        stl_b = result_b[1]

        digest_a = _md5(stl_a)
        digest_b = _md5(stl_b)

        print(f"Original fingerprint MD5: {digest_a}  ({len(stl_a)} bytes)")
        print(f"Alt fingerprint      MD5: {digest_b}  ({len(stl_b)} bytes)")

        assert digest_a != digest_b, "Different fingerprint images should produce different STL output"

    def test_different_zone_produces_different_output(self, synthetic_fingerprint):
        """Zone 1 and zone 2 must yield different STL output."""
        common = dict(
            fingerprint_file=synthetic_fingerprint,
            design_path=get_design_path("PDG040"),
            mode="emboss",
            resolution=80,
        )

        result_z1 = generate_preview_stl(zones=[1], **common)
        result_z2 = generate_preview_stl(zones=[2], **common)

        stl_z1 = result_z1[1]
        stl_z2 = result_z2[2]

        digest_z1 = _md5(stl_z1)
        digest_z2 = _md5(stl_z2)

        print(f"Zone 1 MD5: {digest_z1}  ({len(stl_z1)} bytes)")
        print(f"Zone 2 MD5: {digest_z2}  ({len(stl_z2)} bytes)")

        assert digest_z1 != digest_z2, "Different zones should produce different STL output"

    def test_different_mode_produces_different_output(self, synthetic_fingerprint):
        """Emboss vs. engrave must yield different STL output."""
        common = dict(
            fingerprint_file=synthetic_fingerprint,
            design_path=get_design_path("PDG040"),
            zones=[1],
            resolution=80,
        )

        result_emboss = generate_preview_stl(mode="emboss", **common)
        result_engrave = generate_preview_stl(mode="engrave", **common)

        stl_emboss = result_emboss[1]
        stl_engrave = result_engrave[1]

        digest_emboss = _md5(stl_emboss)
        digest_engrave = _md5(stl_engrave)

        print(f"Emboss  MD5: {digest_emboss}  ({len(stl_emboss)} bytes)")
        print(f"Engrave MD5: {digest_engrave}  ({len(stl_engrave)} bytes)")

        assert digest_emboss != digest_engrave, (
            "Emboss and engrave modes should produce different STL output"
        )
