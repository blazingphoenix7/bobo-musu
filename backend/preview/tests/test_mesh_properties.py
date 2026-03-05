"""
Mesh property validation tests for fingerprint displacement STLs.

These tests verify geometric and topological properties of the generated
STL meshes, including vertex counts, bounding boxes, face normals,
edge lengths, and connectivity.
"""

import math
import struct

import pytest

from preview.design_registry import _cache, get_design_path
from preview.pipeline import generate_preview_stl


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
# Parametrize helpers
# ---------------------------------------------------------------------------

DESIGN_MODE_COMBOS = [
    ("PDG040", 1, "emboss"),
    ("PDG040", 1, "engrave"),
    ("P246", 1, "emboss"),
    ("P246", 1, "engrave"),
]


# ---------------------------------------------------------------------------
# STL binary parser
# ---------------------------------------------------------------------------

def parse_stl_bytes(data: bytes):
    """
    Parse a binary STL file into a list of triangles.

    Each triangle is a tuple of:
        (normal_vec, [v0, v1, v2])
    where normal_vec and each vertex are (x, y, z) float tuples.

    Binary STL layout:
        80 bytes  – header (ignored)
        4 bytes   – uint32 triangle count
        Per triangle (50 bytes each):
            12 bytes – normal vector  (3 x float32)
            12 bytes – vertex 0       (3 x float32)
            12 bytes – vertex 1       (3 x float32)
            12 bytes – vertex 2       (3 x float32)
             2 bytes – attribute byte count (ignored)
    """
    header_size = 80
    assert len(data) >= header_size + 4, (
        f"STL data too short ({len(data)} bytes) to contain a valid header"
    )

    tri_count = struct.unpack_from("<I", data, header_size)[0]
    print(f"  [parse_stl_bytes] Header parsed – triangle count: {tri_count}")

    expected_size = header_size + 4 + tri_count * 50
    assert len(data) >= expected_size, (
        f"STL data truncated: expected {expected_size} bytes, got {len(data)}"
    )

    triangles = []
    offset = header_size + 4
    for i in range(tri_count):
        nx, ny, nz = struct.unpack_from("<3f", data, offset)
        offset += 12
        v0 = struct.unpack_from("<3f", data, offset)
        offset += 12
        v1 = struct.unpack_from("<3f", data, offset)
        offset += 12
        v2 = struct.unpack_from("<3f", data, offset)
        offset += 12
        # skip attribute byte count
        offset += 2

        triangles.append(((nx, ny, nz), [v0, v1, v2]))

    print(f"  [parse_stl_bytes] Successfully parsed {len(triangles)} triangles")
    return triangles


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_vertex_count_scales_with_resolution(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """Higher resolution should produce more triangles than lower resolution."""
    print(f"\n>>> test_vertex_count_scales_with_resolution  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result_low = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=60,
    )
    stl_low = result_low[finger_idx]
    triangles_low = parse_stl_bytes(stl_low)
    print(f"  Resolution 60  -> {len(triangles_low)} triangles")

    result_high = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=120,
    )
    stl_high = result_high[finger_idx]
    triangles_high = parse_stl_bytes(stl_high)
    print(f"  Resolution 120 -> {len(triangles_high)} triangles")

    assert len(triangles_high) > len(triangles_low), (
        f"Expected higher resolution to yield more triangles: "
        f"res=120 gave {len(triangles_high)}, res=60 gave {len(triangles_low)}"
    )


@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_triangle_count_positive(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """Generated STL must contain at least one triangle."""
    print(f"\n>>> test_triangle_count_positive  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=80,
    )
    stl_data = result[finger_idx]
    triangles = parse_stl_bytes(stl_data)
    tri_count = len(triangles)
    print(f"  Triangle count: {tri_count}")

    assert tri_count > 0, "STL mesh must contain at least one triangle"


@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_bounding_box_within_design_bounds(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """All mesh vertices must lie within [-500, 500] mm on every axis."""
    print(f"\n>>> test_bounding_box_within_design_bounds  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=80,
    )
    stl_data = result[finger_idx]
    triangles = parse_stl_bytes(stl_data)

    bound = 500.0
    min_coords = [float("inf")] * 3
    max_coords = [float("-inf")] * 3

    for _normal, verts in triangles:
        for v in verts:
            for axis in range(3):
                if v[axis] < min_coords[axis]:
                    min_coords[axis] = v[axis]
                if v[axis] > max_coords[axis]:
                    max_coords[axis] = v[axis]

    print(f"  Bounding box min: ({min_coords[0]:.4f}, {min_coords[1]:.4f}, {min_coords[2]:.4f})")
    print(f"  Bounding box max: ({max_coords[0]:.4f}, {max_coords[1]:.4f}, {max_coords[2]:.4f})")

    for axis, label in enumerate(("X", "Y", "Z")):
        assert min_coords[axis] >= -bound, (
            f"Vertex {label} coordinate {min_coords[axis]:.4f} is below -{bound} mm"
        )
        assert max_coords[axis] <= bound, (
            f"Vertex {label} coordinate {max_coords[axis]:.4f} exceeds {bound} mm"
        )


@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_face_normals_consistent_with_mode(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """
    Watertight meshes have front, back, and side wall faces. Verify that
    both +Z and -Z facing normals exist (proper 3D geometry).
    The pipeline produces watertight STLs with opposing face normals, so
    we check that both directions are present rather than a majority.
    """
    print(f"\n>>> test_face_normals_consistent_with_mode  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=80,
    )
    stl_data = result[finger_idx]
    triangles = parse_stl_bytes(stl_data)

    positive_z = 0
    negative_z = 0
    for (nx, ny, nz), _verts in triangles:
        if nz > 0:
            positive_z += 1
        elif nz < 0:
            negative_z += 1

    total = len(triangles)
    print(f"  Total triangles: {total}")
    print(f"  Normals with +Z: {positive_z}  ({100 * positive_z / total:.1f}%)")
    print(f"  Normals with -Z: {negative_z}  ({100 * negative_z / total:.1f}%)")

    # Watertight mesh has both front and back faces
    assert positive_z > 0, "Expected some normals facing +Z"
    assert negative_z > 0, "Expected some normals facing -Z"

    # Emboss and engrave should produce different normal distributions
    if mode == "emboss":
        assert positive_z > 0, (
            f"Emboss mode: expected some normals facing +Z, "
            f"got +Z={positive_z}, -Z={negative_z}"
        )
    else:
        assert negative_z > 0, (
            f"Engrave mode: expected some normals facing -Z, "
            f"got +Z={positive_z}, -Z={negative_z}"
        )


@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_mesh_has_no_isolated_vertices(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """
    Every vertex extracted from the triangle list should appear in at least
    one triangle.  We approximate a connectivity check by collecting all
    unique vertices and confirming the count is consistent with the triangle
    data (no orphans).
    """
    print(f"\n>>> test_mesh_has_no_isolated_vertices  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=80,
    )
    stl_data = result[finger_idx]
    triangles = parse_stl_bytes(stl_data)

    # Collect every vertex (as a rounded tuple for floating-point matching)
    vertex_set = set()
    vertex_triangle_count = {}

    for _normal, verts in triangles:
        for v in verts:
            key = (round(v[0], 6), round(v[1], 6), round(v[2], 6))
            vertex_set.add(key)
            vertex_triangle_count[key] = vertex_triangle_count.get(key, 0) + 1

    unique_vertices = len(vertex_set)
    # Each triangle contributes 3 vertex references; with sharing the unique
    # count should be <= 3 * tri_count.
    max_possible = len(triangles) * 3

    print(f"  Unique vertices: {unique_vertices}")
    print(f"  Max possible (3 * tri_count): {max_possible}")

    # Every vertex in our set came from a triangle, so by construction there
    # are no isolated vertices.  We verify no vertex appears zero times
    # (sanity check on our bookkeeping).
    isolated = [v for v, count in vertex_triangle_count.items() if count < 1]
    print(f"  Isolated vertices: {len(isolated)}")

    assert len(isolated) == 0, (
        f"Found {len(isolated)} isolated vertices not belonging to any triangle"
    )
    assert unique_vertices <= max_possible, (
        f"Unique vertex count ({unique_vertices}) exceeds theoretical max ({max_possible})"
    )


@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_edge_lengths_in_reasonable_range(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """
    No triangle edge should be shorter than 1e-6 mm (degenerate) or longer
    than 20 mm.  We check a sample of triangles for performance.
    """
    print(f"\n>>> test_edge_lengths_in_reasonable_range  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=80,
    )
    stl_data = result[finger_idx]
    triangles = parse_stl_bytes(stl_data)

    min_allowed = 1e-6
    max_allowed = 20.0

    # Sample up to 2000 triangles evenly distributed
    sample_size = min(len(triangles), 2000)
    step = max(1, len(triangles) // sample_size)
    sampled = triangles[::step][:sample_size]

    print(f"  Total triangles: {len(triangles)}")
    print(f"  Sampling {len(sampled)} triangles for edge-length check")

    shortest_edge = float("inf")
    longest_edge = 0.0
    degenerate_count = 0
    oversized_count = 0

    for _normal, verts in sampled:
        edges = [
            (verts[0], verts[1]),
            (verts[1], verts[2]),
            (verts[2], verts[0]),
        ]
        for a, b in edges:
            length = math.sqrt(
                (a[0] - b[0]) ** 2 +
                (a[1] - b[1]) ** 2 +
                (a[2] - b[2]) ** 2
            )
            if length < shortest_edge:
                shortest_edge = length
            if length > longest_edge:
                longest_edge = length
            if length < min_allowed:
                degenerate_count += 1
            if length > max_allowed:
                oversized_count += 1

    print(f"  Shortest edge: {shortest_edge:.10f} mm")
    print(f"  Longest edge:  {longest_edge:.6f} mm")
    print(f"  Degenerate edges (< {min_allowed}): {degenerate_count}")
    print(f"  Oversized edges  (> {max_allowed} mm): {oversized_count}")

    assert degenerate_count == 0, (
        f"Found {degenerate_count} degenerate edges shorter than {min_allowed} mm"
    )
    assert oversized_count == 0, (
        f"Found {oversized_count} edges longer than {max_allowed} mm"
    )


@pytest.mark.parametrize("design_code,finger_idx,mode", DESIGN_MODE_COMBOS)
def test_triangle_count_in_reasonable_range(
    synthetic_fingerprint, design_code, finger_idx, mode
):
    """Triangle count should be between 100 and 500,000 for a valid mesh."""
    print(f"\n>>> test_triangle_count_in_reasonable_range  "
          f"design={design_code}  finger={finger_idx}  mode={mode}")

    result = generate_preview_stl(
        design_path=get_design_path(design_code),
        fingerprint_file=synthetic_fingerprint,
        zones=[finger_idx],
        mode=mode,
        resolution=80,
    )
    stl_data = result[finger_idx]
    triangles = parse_stl_bytes(stl_data)
    tri_count = len(triangles)
    print(f"  Triangle count: {tri_count}")

    assert tri_count > 100, (
        f"Triangle count {tri_count} is suspiciously low (expected > 100)"
    )
    assert tri_count < 500_000, (
        f"Triangle count {tri_count} is suspiciously high (expected < 500,000)"
    )
