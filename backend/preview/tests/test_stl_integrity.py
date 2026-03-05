"""
Binary STL integrity tests for the fingerprint preview pipeline.

These tests exercise generate_preview_stl directly (not through the API)
and validate that the returned bytes constitute a well-formed binary STL file.

Binary STL format reference:
  - 80-byte header (arbitrary)
  - 4-byte uint32 LE triangle count
  - N x 50-byte triangle records:
        12 bytes  normal  (3 x float32)
        12 bytes  vertex1 (3 x float32)
        12 bytes  vertex2 (3 x float32)
        12 bytes  vertex3 (3 x float32)
         2 bytes  attribute byte count (uint16)
  Total file size = 80 + 4 + (50 * triangle_count)
"""

import math
import struct

import pytest

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


# ---------------------------------------------------------------------------
# Parametrize matrix
# ---------------------------------------------------------------------------

DESIGN_ZONE_MODE = [
    ("PDG040", 1, "emboss"),
    ("PDG040", 1, "engrave"),
    ("P246", 1, "emboss"),
    ("P246", 1, "engrave"),
    ("PDG040", 2, "emboss"),
    ("P246", 2, "engrave"),
]


# ---------------------------------------------------------------------------
# Helper – generate STL bytes for a given parameter combo
# ---------------------------------------------------------------------------

def _generate_stl(synthetic_fingerprint, design_code, zone, mode):
    """Call the pipeline and return raw STL bytes."""
    design_path = get_design_path(design_code)
    fingerprint_path = synthetic_fingerprint
    print(f"Design path : {design_path}")
    print(f"Fingerprint : {fingerprint_path}")
    print(f"Zone        : {zone}")
    print(f"Mode        : {mode}")
    result = generate_preview_stl(
        design_path,
        fingerprint_path,
        [zone],
        mode=mode,
        resolution=80,
    )
    stl_bytes = result[zone]
    print(f"STL size    : {len(stl_bytes)} bytes")
    return stl_bytes


def _parse_triangle_count(stl_bytes):
    """Read the uint32 LE triangle count at offset 80."""
    return struct.unpack_from("<I", stl_bytes, 80)[0]


def _iter_triangles(stl_bytes):
    """Yield (normal, v1, v2, v3, attr) tuples from a binary STL buffer."""
    tri_count = _parse_triangle_count(stl_bytes)
    offset = 84
    for i in range(tri_count):
        record = struct.unpack_from("<12f H", stl_bytes, offset)
        normal = record[0:3]
        v1 = record[3:6]
        v2 = record[6:9]
        v3 = record[9:12]
        attr = record[12]
        offset += 50
        yield normal, v1, v2, v3, attr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_has_80_byte_header(synthetic_fingerprint, design_code, zone, mode):
    """The STL must begin with an 80-byte header."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    print(f"Total length: {len(stl_bytes)}")
    assert len(stl_bytes) >= 80, (
        f"STL is only {len(stl_bytes)} bytes – too short for the 80-byte header"
    )
    print("Header (first 80 bytes) present: OK")


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_triangle_count_field_matches_actual(
    synthetic_fingerprint, design_code, zone, mode
):
    """The uint32 LE at bytes 80-83 must match the number of 50-byte records
    that follow."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    data_section = len(stl_bytes) - 84
    actual_records = data_section // 50
    remainder = data_section % 50
    print(f"Declared triangle count : {tri_count}")
    print(f"Actual 50-byte records  : {actual_records}")
    print(f"Remainder bytes         : {remainder}")
    assert remainder == 0, (
        f"Data section has {remainder} leftover bytes after dividing by 50"
    )
    assert tri_count == actual_records, (
        f"Header says {tri_count} triangles but data contains {actual_records} records"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_file_size_matches_formula(
    synthetic_fingerprint, design_code, zone, mode
):
    """Total file size must equal 80 + 4 + (50 * tri_count)."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    expected_size = 80 + 4 + (50 * tri_count)
    actual_size = len(stl_bytes)
    print(f"Triangle count : {tri_count}")
    print(f"Expected size  : {expected_size}")
    print(f"Actual size    : {actual_size}")
    assert actual_size == expected_size, (
        f"Size mismatch: expected {expected_size}, got {actual_size}"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_all_triangles_readable(
    synthetic_fingerprint, design_code, zone, mode
):
    """Every declared triangle record must be fully readable."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    read_count = 0
    for normal, v1, v2, v3, attr in _iter_triangles(stl_bytes):
        read_count += 1
    print(f"Declared triangles : {tri_count}")
    print(f"Read triangles     : {read_count}")
    assert read_count == tri_count, (
        f"Could only read {read_count} of {tri_count} triangles"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_no_nan_values(synthetic_fingerprint, design_code, zone, mode):
    """No float value in any triangle record should be NaN."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    nan_locations = []
    for idx, (normal, v1, v2, v3, _attr) in enumerate(_iter_triangles(stl_bytes)):
        for label, vec in [("normal", normal), ("v1", v1), ("v2", v2), ("v3", v3)]:
            for comp_idx, val in enumerate(vec):
                if math.isnan(val):
                    nan_locations.append(
                        f"triangle {idx}, {label}[{comp_idx}]"
                    )
    print(f"Triangles scanned : {tri_count}")
    print(f"NaN occurrences   : {len(nan_locations)}")
    if nan_locations:
        for loc in nan_locations[:20]:
            print(f"  NaN at {loc}")
    assert len(nan_locations) == 0, (
        f"Found {len(nan_locations)} NaN value(s) in STL floats"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_no_inf_values(synthetic_fingerprint, design_code, zone, mode):
    """No float value in any triangle record should be Inf."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    inf_locations = []
    for idx, (normal, v1, v2, v3, _attr) in enumerate(_iter_triangles(stl_bytes)):
        for label, vec in [("normal", normal), ("v1", v1), ("v2", v2), ("v3", v3)]:
            for comp_idx, val in enumerate(vec):
                if math.isinf(val):
                    inf_locations.append(
                        f"triangle {idx}, {label}[{comp_idx}] = {val}"
                    )
    print(f"Triangles scanned : {tri_count}")
    print(f"Inf occurrences   : {len(inf_locations)}")
    if inf_locations:
        for loc in inf_locations[:20]:
            print(f"  Inf at {loc}")
    assert len(inf_locations) == 0, (
        f"Found {len(inf_locations)} Inf value(s) in STL floats"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_vertices_in_reasonable_range(
    synthetic_fingerprint, design_code, zone, mode
):
    """All vertex coordinates must lie within [-1000, 1000]."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    out_of_range = []
    for idx, (_normal, v1, v2, v3, _attr) in enumerate(_iter_triangles(stl_bytes)):
        for label, vec in [("v1", v1), ("v2", v2), ("v3", v3)]:
            for comp_idx, val in enumerate(vec):
                if val < -1000.0 or val > 1000.0:
                    out_of_range.append(
                        f"triangle {idx}, {label}[{comp_idx}] = {val}"
                    )
    print(f"Triangles scanned      : {tri_count}")
    print(f"Out-of-range vertices  : {len(out_of_range)}")
    if out_of_range:
        for loc in out_of_range[:20]:
            print(f"  {loc}")
    assert len(out_of_range) == 0, (
        f"Found {len(out_of_range)} vertex coordinate(s) outside [-1000, 1000]"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_normals_are_nonzero(
    synthetic_fingerprint, design_code, zone, mode
):
    """Each triangle normal should be non-zero (pipeline writes raw cross-product
    normals which are not unit-length, but should have non-zero magnitude for
    non-degenerate triangles)."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    zero_normals = 0
    for idx, (normal, _v1, _v2, _v3, _attr) in enumerate(_iter_triangles(stl_bytes)):
        nx, ny, nz = normal
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length == 0.0:
            zero_normals += 1
    print(f"Triangles scanned : {tri_count}")
    print(f"Zero normals      : {zero_normals}")
    # Allow up to 1% zero normals (near-degenerate triangles at boundaries)
    max_allowed = max(1, int(tri_count * 0.01))
    assert zero_normals <= max_allowed, (
        f"Found {zero_normals} zero normals (max allowed: {max_allowed})"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_no_degenerate_triangles(
    synthetic_fingerprint, design_code, zone, mode
):
    """Each triangle must have an area greater than 1e-10 (not degenerate)."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    degenerate = []
    for idx, (_normal, v1, v2, v3, _attr) in enumerate(_iter_triangles(stl_bytes)):
        # edge vectors
        e1 = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
        e2 = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
        # cross product
        cx = e1[1] * e2[2] - e1[2] * e2[1]
        cy = e1[2] * e2[0] - e1[0] * e2[2]
        cz = e1[0] * e2[1] - e1[1] * e2[0]
        area = 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)
        if area <= 1e-10:
            degenerate.append(
                f"triangle {idx}: area={area:.2e}, "
                f"v1=({v1[0]:.4f},{v1[1]:.4f},{v1[2]:.4f}), "
                f"v2=({v2[0]:.4f},{v2[1]:.4f},{v2[2]:.4f}), "
                f"v3=({v3[0]:.4f},{v3[1]:.4f},{v3[2]:.4f})"
            )
    print(f"Triangles scanned   : {tri_count}")
    print(f"Degenerate triangles: {len(degenerate)}")
    if degenerate:
        for entry in degenerate[:20]:
            print(f"  {entry}")
    assert len(degenerate) == 0, (
        f"Found {len(degenerate)} degenerate triangle(s) with area <= 1e-10"
    )


@pytest.mark.parametrize("design_code,zone,mode", DESIGN_ZONE_MODE)
def test_stl_triangle_count_nonzero(
    synthetic_fingerprint, design_code, zone, mode
):
    """The STL must contain at least one triangle."""
    stl_bytes = _generate_stl(synthetic_fingerprint, design_code, zone, mode)
    tri_count = _parse_triangle_count(stl_bytes)
    print(f"Triangle count: {tri_count}")
    assert tri_count > 0, "STL contains zero triangles"
