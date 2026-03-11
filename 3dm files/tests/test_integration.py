"""Integration tests: full pipeline against real .3dm files."""
import sys
import struct
import pytest
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import rhino3dm
from fingerprint_displace import (
    PipelineError,
    detect_zones,
    find_zone_face,
    find_zone_body,
    process_zone,
    export_stl,
    generate_test_fingerprint,
    preprocess_fingerprint,
)

DESIGNS_DIR = Path(__file__).parent.parent / "designs"

DESIGN_CONFIGS = [
    {"file": "PDG040.3dm", "expected_zones": [1, 2, 3, 4, 5], "id": "PDG040"},
    {"file": "P246442LY.3dm", "expected_zones": [1, 2], "id": "P246"},
]

# Add AAP10985F if available
if (DESIGNS_DIR / "AAP10985F.3dm").exists():
    DESIGN_CONFIGS.append(
        {"file": "AAP10985F.3dm", "expected_zones": None, "id": "AAP10985F"}
    )


def _load_model(design_id):
    """Load a model by design id, skip if file missing."""
    for cfg in DESIGN_CONFIGS:
        if cfg["id"] == design_id:
            path = DESIGNS_DIR / cfg["file"]
            if not path.exists():
                pytest.skip(f"Design file not found: {path}")
            model = rhino3dm.File3dm.Read(str(path))
            if model is None:
                pytest.skip(f"Could not read design file: {path}")
            return model
    pytest.skip(f"Design config not found for id: {design_id}")


def _load_model_from_cfg(cfg):
    """Load a model from a DESIGN_CONFIGS entry, skip if file missing."""
    path = DESIGNS_DIR / cfg["file"]
    if not path.exists():
        pytest.skip(f"Design file not found: {path}")
    model = rhino3dm.File3dm.Read(str(path))
    if model is None:
        pytest.skip(f"Could not read design file: {path}")
    return model


@pytest.fixture(scope="session")
def synth_fp():
    """Session-scoped synthetic fingerprint for integration tests."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_path = f.name
    try:
        generate_test_fingerprint(tmp_path, size=256)
        img = preprocess_fingerprint(tmp_path, target_size=256)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return img


# ── TestZoneDetection ──────────────────────────────────────────────────

class TestZoneDetection:

    @pytest.mark.parametrize("cfg", DESIGN_CONFIGS, ids=[c["id"] for c in DESIGN_CONFIGS])
    def test_detects_expected_zones(self, cfg):
        """detect_zones returns expected zone list (or at least 1 for AAP)."""
        model = _load_model_from_cfg(cfg)
        zones = detect_zones(model)

        if cfg["expected_zones"] is not None:
            assert zones == cfg["expected_zones"], (
                f"{cfg['id']}: expected zones {cfg['expected_zones']}, got {zones}"
            )
        else:
            # AAP or unknown — just verify at least one zone found
            assert len(zones) >= 1, (
                f"{cfg['id']}: expected at least 1 zone, got {zones}"
            )


# ── TestFullPipeline ───────────────────────────────────────────────────

class TestFullPipeline:

    @pytest.mark.parametrize("cfg", DESIGN_CONFIGS, ids=[c["id"] for c in DESIGN_CONFIGS])
    def test_process_all_zones(self, cfg, synth_fp):
        """Process every zone at resolution=80; display_mesh > 0 verts/faces,
        stl_mesh has more vertices than display_mesh."""
        model = _load_model_from_cfg(cfg)
        zones = detect_zones(model)
        assert len(zones) >= 1, f"{cfg['id']}: no zones detected"

        for zone_num in zones:
            display_mesh, stl_mesh, face_brep, body_brep = process_zone(
                model, zone_num, synth_fp,
                depth=0.3, resolution=80, mode="emboss",
                feather_cells=5, do_stl=True,
            )

            assert display_mesh is not None, (
                f"{cfg['id']} zone {zone_num}: display_mesh is None"
            )
            assert display_mesh.Faces.Count > 0, (
                f"{cfg['id']} zone {zone_num}: display_mesh has 0 faces"
            )
            assert len(display_mesh.Vertices) > 0, (
                f"{cfg['id']} zone {zone_num}: display_mesh has 0 vertices"
            )

            assert stl_mesh is not None, (
                f"{cfg['id']} zone {zone_num}: stl_mesh is None"
            )
            assert len(stl_mesh.Vertices) > len(display_mesh.Vertices), (
                f"{cfg['id']} zone {zone_num}: stl_mesh should have more vertices than "
                f"display_mesh (watertight adds side/bottom walls). "
                f"stl={len(stl_mesh.Vertices)}, display={len(display_mesh.Vertices)}"
            )

    @pytest.mark.parametrize("cfg", DESIGN_CONFIGS, ids=[c["id"] for c in DESIGN_CONFIGS])
    def test_engrave_mode(self, cfg, synth_fp):
        """Process first zone in engrave mode; output is non-empty."""
        model = _load_model_from_cfg(cfg)
        zones = detect_zones(model)
        assert len(zones) >= 1, f"{cfg['id']}: no zones detected"

        zone_num = zones[0]
        display_mesh, stl_mesh, face_brep, body_brep = process_zone(
            model, zone_num, synth_fp,
            depth=0.3, resolution=80, mode="engrave",
            feather_cells=5, do_stl=False,
        )

        assert display_mesh is not None, (
            f"{cfg['id']} zone {zone_num}: engrave display_mesh is None"
        )
        assert display_mesh.Faces.Count > 0, (
            f"{cfg['id']} zone {zone_num}: engrave display_mesh has 0 faces"
        )
        assert len(display_mesh.Vertices) > 0, (
            f"{cfg['id']} zone {zone_num}: engrave display_mesh has 0 vertices"
        )

    @pytest.mark.parametrize("cfg", DESIGN_CONFIGS, ids=[c["id"] for c in DESIGN_CONFIGS])
    def test_stl_export(self, cfg, synth_fp, tmp_path):
        """Export STL for first zone; validate binary STL structure."""
        model = _load_model_from_cfg(cfg)
        zones = detect_zones(model)
        assert len(zones) >= 1, f"{cfg['id']}: no zones detected"

        zone_num = zones[0]
        display_mesh, stl_mesh, face_brep, body_brep = process_zone(
            model, zone_num, synth_fp,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=True,
        )

        assert stl_mesh is not None, f"{cfg['id']}: stl_mesh is None"

        stl_path = tmp_path / f"{cfg['id']}_zone{zone_num}.stl"
        export_stl(stl_mesh, str(stl_path))

        assert stl_path.exists(), f"STL file not created at {stl_path}"

        # Validate binary STL structure:
        # - 80-byte header
        # - 4-byte uint32 triangle count
        # - 50 bytes per triangle (12 normal + 36 vertex + 2 attribute)
        data = stl_path.read_bytes()
        assert len(data) >= 84, f"STL file too small: {len(data)} bytes"

        tri_count = struct.unpack_from("<I", data, 80)[0]
        assert tri_count > 0, f"{cfg['id']}: STL has 0 triangles"

        expected_size = 80 + 4 + tri_count * 50
        assert len(data) == expected_size, (
            f"{cfg['id']}: STL file size mismatch. "
            f"Expected {expected_size} bytes for {tri_count} triangles, "
            f"got {len(data)} bytes"
        )


# ── TestRegressionExistingDesigns ──────────────────────────────────────

class TestRegressionExistingDesigns:

    def test_pdg040_zone1_vertex_count_stable(self, synth_fp):
        """PDG040 zone 1 at res=80 should have 100 < vertices < 6400."""
        model = _load_model("PDG040")
        display_mesh, stl_mesh, _, _ = process_zone(
            model, 1, synth_fp,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )

        vcount = len(display_mesh.Vertices)
        assert vcount > 100, f"PDG040 zone 1: too few vertices ({vcount}), expected > 100"
        assert vcount < 6400, f"PDG040 zone 1: too many vertices ({vcount}), expected < 6400"

    def test_p246_zone1_vertex_count_stable(self, synth_fp):
        """P246 zone 1 at res=80 should have 100 < vertices < 6400."""
        model = _load_model("P246")
        display_mesh, stl_mesh, _, _ = process_zone(
            model, 1, synth_fp,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
        )

        vcount = len(display_mesh.Vertices)
        assert vcount > 100, f"P246 zone 1: too few vertices ({vcount}), expected > 100"
        assert vcount < 6400, f"P246 zone 1: too many vertices ({vcount}), expected < 6400"


# ── TestUnifiedMode ────────────────────────────────────────────────────

class TestUnifiedMode:

    def test_unified_mapping_pdg040(self, synth_fp):
        """PDG040 with unified=True: compute global_cx/cy/scale from all zones,
        process zone 1, verify non-empty mesh."""
        model = _load_model("PDG040")
        zones = detect_zones(model)
        assert len(zones) >= 1, "PDG040: no zones detected"

        # Compute unified (global) bounding box from all zone FACE surfaces
        combined_min_x = float("inf")
        combined_max_x = float("-inf")
        combined_min_y = float("inf")
        combined_max_y = float("-inf")

        for z in zones:
            _, _, face_brep = find_zone_face(model, z)
            bb = face_brep.GetBoundingBox()
            combined_min_x = min(combined_min_x, bb.Min.X)
            combined_max_x = max(combined_max_x, bb.Max.X)
            combined_min_y = min(combined_min_y, bb.Min.Y)
            combined_max_y = max(combined_max_y, bb.Max.Y)

        global_cx = (combined_min_x + combined_max_x) / 2
        global_cy = (combined_min_y + combined_max_y) / 2
        global_half_x = (combined_max_x - combined_min_x) / 2
        global_half_y = (combined_max_y - combined_min_y) / 2
        global_scale = max(global_half_x, global_half_y) * 1.05

        # Sanity check: global_scale should be positive
        assert global_scale > 0, f"global_scale must be positive, got {global_scale}"

        # Process zone 1 with unified mapping
        display_mesh, stl_mesh, face_brep, body_brep = process_zone(
            model, 1, synth_fp,
            depth=0.3, resolution=80, mode="emboss",
            feather_cells=5, do_stl=False,
            global_cx=global_cx, global_cy=global_cy, global_scale=global_scale,
        )

        assert display_mesh is not None, "PDG040 unified zone 1: display_mesh is None"
        assert display_mesh.Faces.Count > 0, (
            "PDG040 unified zone 1: display_mesh has 0 faces"
        )
        assert len(display_mesh.Vertices) > 0, (
            "PDG040 unified zone 1: display_mesh has 0 vertices"
        )
