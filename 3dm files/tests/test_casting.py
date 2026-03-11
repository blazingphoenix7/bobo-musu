"""Tests for casting-related pipeline functions (3D boundary extraction)."""
import os
import sys
import math
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rhino3dm
from fingerprint_displace import (
    extract_trim_boundary,
    extract_trim_boundary_3d,
    find_zone_face,
    find_zone_body,
    detect_zones,
)


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

        # Both should have points; extract XY from 3D for comparison
        xy_from_3d = set()
        for pt in boundary_3d:
            xy_from_3d.add((round(pt[0], 3), round(pt[1], 3)))

        xy_from_2d = set()
        for pt in boundary_2d:
            xy_from_2d.add((round(pt[0], 3), round(pt[1], 3)))

        # The 3D version uses edge-walk (no angle sort) while 2D uses angle sort,
        # so the point sets should overlap significantly even if order differs
        overlap = xy_from_2d & xy_from_3d
        overlap_ratio = len(overlap) / max(len(xy_from_2d), 1)
        assert overlap_ratio > 0.5, (
            f"XY overlap too low: {overlap_ratio:.2f} "
            f"(2D has {len(xy_from_2d)} unique, 3D has {len(xy_from_3d)} unique, "
            f"{len(overlap)} in common)"
        )
