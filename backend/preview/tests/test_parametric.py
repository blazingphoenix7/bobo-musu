"""
Parametric cross-combo tests for the fingerprint displacement pipeline.

Every combination of (design_id, zone, mode) in ALL_COMBOS is tested
against multiple validity criteria: output structure, triangle count,
binary STL format, NaN-free vertices, coordinate bounds, and file size.
"""

import struct
import math

import numpy as np
import pytest

from preview.pipeline import generate_preview_stl
from preview.design_registry import get_design_path, _cache


ALL_COMBOS = [
    ("PDG040", 1, "emboss"), ("PDG040", 1, "engrave"),
    ("PDG040", 2, "emboss"), ("PDG040", 2, "engrave"),
    ("PDG040", 3, "emboss"), ("PDG040", 3, "engrave"),
    ("PDG040", 4, "emboss"), ("PDG040", 4, "engrave"),
    ("PDG040", 5, "emboss"), ("PDG040", 5, "engrave"),
    ("P246", 1, "emboss"), ("P246", 1, "engrave"),
    ("P246", 2, "emboss"), ("P246", 2, "engrave"),
]

RESOLUTION = 80


@pytest.fixture(autouse=True)
def clear_design_cache():
    """Clear the design registry cache before every test to ensure isolation."""
    _cache.clear()
    yield
    _cache.clear()


def _parse_tri_count(stl_bytes: bytes) -> int:
    """Parse the triangle count from a binary STL header (bytes 80-84)."""
    return struct.unpack("<I", stl_bytes[80:84])[0]


def _parse_all_vertex_floats(stl_bytes: bytes) -> list:
    """
    Parse every vertex float from a binary STL file.

    Binary STL layout per triangle (50 bytes each):
      - 12 bytes: normal vector  (3 x float32)
      - 36 bytes: 3 vertices     (9 x float32)
      -  2 bytes: attribute byte count

    Returns a flat list of all vertex coordinate floats.
    """
    tri_count = _parse_tri_count(stl_bytes)
    vertex_floats = []
    offset = 84  # skip 80-byte header + 4-byte triangle count

    for i in range(tri_count):
        # Skip 12-byte normal vector
        normal_offset = offset + 12
        # Read 3 vertices x 3 floats = 9 floats
        for v in range(9):
            float_offset = normal_offset + v * 4
            value = struct.unpack("<f", stl_bytes[float_offset:float_offset + 4])[0]
            vertex_floats.append(value)
        offset += 50  # advance to next triangle

    return vertex_floats


# ---------------------------------------------------------------------------
# Parametrized tests — one run per (design_id, zone, mode) combo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_returns_valid_output(
    synthetic_fingerprint, design_id, zone, mode
):
    """generate_preview_stl must return a dict with the zone key mapping to bytes > 100."""
    print(f"\n[test_every_combo_returns_valid_output] design={design_id} zone={zone} mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    print(f"  Result type: {type(result)}")
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"

    zone_key = zone
    assert zone_key in result, f"Zone key {zone_key} not found in result keys: {list(result.keys())}"

    stl_bytes = result[zone_key]
    print(f"  STL bytes length: {len(stl_bytes)}")
    assert isinstance(stl_bytes, bytes), f"Expected bytes for zone {zone_key}, got {type(stl_bytes)}"
    assert len(stl_bytes) > 100, (
        f"STL output too small ({len(stl_bytes)} bytes) for "
        f"design={design_id} zone={zone} mode={mode}"
    )


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_returns_nonzero_triangles(
    synthetic_fingerprint, design_id, zone, mode
):
    """The binary STL must contain at least one triangle."""
    print(f"\n[test_every_combo_returns_nonzero_triangles] design={design_id} zone={zone} mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    stl_bytes = result[zone]
    tri_count = _parse_tri_count(stl_bytes)
    print(f"  Triangle count: {tri_count}")
    assert tri_count > 0, (
        f"Zero triangles in STL for design={design_id} zone={zone} mode={mode}"
    )


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_stl_is_valid_binary(
    synthetic_fingerprint, design_id, zone, mode
):
    """Binary STL size must equal 80 + 4 + (50 * tri_count)."""
    print(f"\n[test_every_combo_stl_is_valid_binary] design={design_id} zone={zone} mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    stl_bytes = result[zone]
    tri_count = _parse_tri_count(stl_bytes)
    expected_size = 80 + 4 + (50 * tri_count)
    actual_size = len(stl_bytes)

    print(f"  Triangle count: {tri_count}")
    print(f"  Expected size:  {expected_size}")
    print(f"  Actual size:    {actual_size}")

    assert expected_size == actual_size, (
        f"Binary STL size mismatch: expected {expected_size} bytes "
        f"(80 + 4 + 50*{tri_count}), got {actual_size} bytes "
        f"for design={design_id} zone={zone} mode={mode}"
    )


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_no_nan_vertices(
    synthetic_fingerprint, design_id, zone, mode
):
    """No vertex coordinate in the STL may be NaN."""
    print(f"\n[test_every_combo_no_nan_vertices] design={design_id} zone={zone} mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    stl_bytes = result[zone]
    vertex_floats = _parse_all_vertex_floats(stl_bytes)
    nan_count = sum(1 for v in vertex_floats if math.isnan(v))

    print(f"  Total vertex floats: {len(vertex_floats)}")
    print(f"  NaN count:           {nan_count}")

    assert nan_count == 0, (
        f"Found {nan_count} NaN values among {len(vertex_floats)} vertex floats "
        f"for design={design_id} zone={zone} mode={mode}"
    )


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_vertices_in_bounds(
    synthetic_fingerprint, design_id, zone, mode
):
    """All vertex coordinates must fall within [-500, 500]."""
    print(f"\n[test_every_combo_vertices_in_bounds] design={design_id} zone={zone} mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    stl_bytes = result[zone]
    vertex_floats = _parse_all_vertex_floats(stl_bytes)
    coords = np.array(vertex_floats, dtype=np.float32)

    if len(coords) > 0:
        min_val = float(np.min(coords))
        max_val = float(np.max(coords))
    else:
        min_val = 0.0
        max_val = 0.0

    print(f"  Vertex float count: {len(coords)}")
    print(f"  Min coordinate:     {min_val}")
    print(f"  Max coordinate:     {max_val}")

    assert min_val >= -500.0, (
        f"Vertex coordinate {min_val} below -500 "
        f"for design={design_id} zone={zone} mode={mode}"
    )
    assert max_val <= 500.0, (
        f"Vertex coordinate {max_val} above 500 "
        f"for design={design_id} zone={zone} mode={mode}"
    )


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_has_reasonable_triangle_count(
    synthetic_fingerprint, design_id, zone, mode
):
    """Triangle count must be between 100 and 500,000."""
    print(f"\n[test_every_combo_has_reasonable_triangle_count] design={design_id} zone={zone} mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    stl_bytes = result[zone]
    tri_count = _parse_tri_count(stl_bytes)

    print(f"  Triangle count: {tri_count}")

    assert tri_count > 100, (
        f"Too few triangles ({tri_count}) "
        f"for design={design_id} zone={zone} mode={mode}"
    )
    assert tri_count < 500_000, (
        f"Too many triangles ({tri_count}) "
        f"for design={design_id} zone={zone} mode={mode}"
    )


@pytest.mark.parametrize("design_id,zone,mode", ALL_COMBOS)
def test_every_combo_stl_file_size_reasonable(
    synthetic_fingerprint, design_id, zone, mode
):
    """STL file size must be between 100 bytes and 50 MB."""
    print(f"\n[test_every_combo_stl_file_size_reasonable] design={design_id} zone={zone} mode={mode}")

    max_size = 50 * 1024 * 1024  # 50 MB

    result = generate_preview_stl(
        design_path=get_design_path(design_id),
        fingerprint_file=synthetic_fingerprint,
        zones=[zone],
        mode=mode,
        resolution=RESOLUTION,
    )

    stl_bytes = result[zone]
    size = len(stl_bytes)

    print(f"  File size: {size} bytes ({size / 1024:.1f} KB)")

    assert size > 100, (
        f"STL file too small ({size} bytes) "
        f"for design={design_id} zone={zone} mode={mode}"
    )
    assert size < max_size, (
        f"STL file too large ({size} bytes, {size / 1024 / 1024:.1f} MB) "
        f"for design={design_id} zone={zone} mode={mode}"
    )


# ---------------------------------------------------------------------------
# Non-parametrized aggregate tests
# ---------------------------------------------------------------------------


def test_emboss_engrave_pairs_have_same_triangle_count(synthetic_fingerprint):
    """
    For each (design_id, zone) pair, emboss and engrave modes must produce
    the same triangle count — the displacement direction changes but not
    the mesh topology.
    """
    print("\n[test_emboss_engrave_pairs_have_same_triangle_count]")

    # Collect unique (design_id, zone) pairs
    pairs = set()
    for design_id, zone, mode in ALL_COMBOS:
        pairs.add((design_id, zone))

    for design_id, zone in sorted(pairs):
        print(f"  Checking design={design_id} zone={zone} ...")

        result_emboss = generate_preview_stl(
            design_path=get_design_path(design_id),
            fingerprint_file=synthetic_fingerprint,
            zones=[zone],
            mode="emboss",
            resolution=RESOLUTION,
        )
        result_engrave = generate_preview_stl(
            design_path=get_design_path(design_id),
            fingerprint_file=synthetic_fingerprint,
            zones=[zone],
            mode="engrave",
            resolution=RESOLUTION,
        )

        emboss_tri = _parse_tri_count(result_emboss[zone])
        engrave_tri = _parse_tri_count(result_engrave[zone])

        print(f"    emboss triangles:  {emboss_tri}")
        print(f"    engrave triangles: {engrave_tri}")

        assert emboss_tri == engrave_tri, (
            f"Triangle count mismatch for design={design_id} zone={zone}: "
            f"emboss={emboss_tri}, engrave={engrave_tri}"
        )


def test_all_designs_all_zones_processable(synthetic_fingerprint):
    """
    Every single combination in ALL_COMBOS must succeed without raising
    an exception. This is a smoke test across the full matrix.
    """
    print("\n[test_all_designs_all_zones_processable]")

    failures = []

    for design_id, zone, mode in ALL_COMBOS:
        print(f"  Processing design={design_id} zone={zone} mode={mode} ...")
        try:
            result = generate_preview_stl(
                design_path=get_design_path(design_id),
                fingerprint_file=synthetic_fingerprint,
                zones=[zone],
                mode=mode,
                resolution=RESOLUTION,
            )
            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            assert zone in result, f"Zone key {zone} missing from result"
            assert len(result[zone]) > 0, "Empty STL bytes"
            print(f"    OK — {len(result[zone])} bytes")
        except Exception as exc:
            failure_msg = (
                f"design={design_id} zone={zone} mode={mode}: "
                f"{type(exc).__name__}: {exc}"
            )
            print(f"    FAILED — {failure_msg}")
            failures.append(failure_msg)

    if failures:
        joined = "\n  ".join(failures)
        pytest.fail(
            f"{len(failures)} combo(s) failed out of {len(ALL_COMBOS)}:\n  {joined}"
        )

    print(f"  All {len(ALL_COMBOS)} combinations processed successfully.")
