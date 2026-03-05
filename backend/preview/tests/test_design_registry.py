"""Tests for the design registry module."""
import pytest
from django.conf import settings
from preview.design_registry import (
    get_designs, get_design, get_design_path, get_zone_count, _cache
)


@pytest.fixture(autouse=True)
def clear_registry_cache():
    """Clear the design registry cache before each test."""
    _cache.clear()
    yield
    _cache.clear()


class TestDesignRegistryLoading:
    def test_all_designs_load(self):
        """designs.json parses without error and returns designs."""
        designs = get_designs()
        print(f"  Loaded {len(designs)} designs")
        assert len(designs) >= 1, "Expected at least 1 design"
        for d in designs:
            print(f"    {d['id']}: {d['display_name']} ({len(d['zones'])} zones)")
            assert "id" in d, f"Design missing 'id': {d}"
            assert "display_name" in d, f"Design missing 'display_name': {d}"
            assert "filename" in d, f"Design missing 'filename': {d}"
            assert "zones" in d, f"Design missing 'zones': {d}"

    def test_zone_autodetection_matches_known_counts(self):
        """PDG040 has 5 zones, P246 has 2 zones."""
        pdg = get_design("PDG040")
        assert pdg is not None, "PDG040 design not found"
        zone_nums = [z["number"] for z in pdg["zones"]]
        print(f"  PDG040 zones: {zone_nums}")
        assert zone_nums == [1, 2, 3, 4, 5], f"Expected [1,2,3,4,5], got {zone_nums}"

        p246 = get_design("P246")
        assert p246 is not None, "P246 design not found"
        zone_nums = [z["number"] for z in p246["zones"]]
        print(f"  P246 zones: {zone_nums}")
        assert zone_nums == [1, 2], f"Expected [1,2], got {zone_nums}"

    def test_zone_numbers_are_sorted(self):
        """For each design: zones list is sorted ascending."""
        for design in get_designs():
            zone_nums = [z["number"] for z in design["zones"]]
            print(f"  {design['id']} zones: {zone_nums}")
            assert zone_nums == sorted(zone_nums), (
                f"{design['id']} zones not sorted: {zone_nums}"
            )

    def test_design_files_exist_on_disk(self):
        """For each design in config: .3dm file exists at expected path."""
        for design in get_designs():
            path = get_design_path(design["id"])
            print(f"  {design['id']}: {path}")
            assert path is not None, f"No path for {design['id']}"
            assert path.exists(), f"File not found: {path}"
            assert path.is_file(), f"Not a file: {path}"

    def test_get_design_returns_none_for_invalid_id(self):
        """get_design('NONEXISTENT') returns None."""
        result = get_design("NONEXISTENT")
        print(f"  get_design('NONEXISTENT') = {result}")
        assert result is None

    def test_get_design_path_returns_valid_path(self):
        """For each design: path exists and is a file."""
        for design in get_designs():
            path = get_design_path(design["id"])
            print(f"  {design['id']}: {path}")
            assert path is not None
            assert path.exists()
            assert path.is_file()

    def test_zone_geometry_cache_consistency(self):
        """Call get_design() twice \u2192 cached, zone metadata identical."""
        d1 = get_design("PDG040")
        d2 = get_design("PDG040")
        assert d1 is d2, "Expected cached object (same reference)"
        z1 = [z["number"] for z in d1["zones"]]
        z2 = [z["number"] for z in d2["zones"]]
        print(f"  Call 1 zones: {z1}")
        print(f"  Call 2 zones: {z2}")
        assert z1 == z2

    def test_designs_json_schema_valid(self):
        """Every entry has required fields; no duplicate IDs or filenames."""
        designs = get_designs()
        ids = [d["id"] for d in designs]
        filenames = [d["filename"] for d in designs]
        print(f"  IDs: {ids}")
        print(f"  Filenames: {filenames}")
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"
        assert len(filenames) == len(set(filenames)), f"Duplicate filenames: {filenames}"
        for d in designs:
            assert isinstance(d["id"], str) and len(d["id"]) > 0
            assert isinstance(d["display_name"], str) and len(d["display_name"]) > 0
            assert isinstance(d["zones"], list) and len(d["zones"]) > 0

    def test_registry_survives_missing_3dm_file(self, tmp_path):
        """If a designs.json entry points to a nonexistent file, registry still loads."""
        import json
        # Create a temporary designs.json with a bad entry
        bad_config = {
            "designs": [
                {
                    "id": "GHOST",
                    "filename": "nonexistent.3dm",
                    "display_name": "Ghost Design",
                    "description": "Does not exist"
                }
            ]
        }
        bad_path = tmp_path / "bad_designs.json"
        bad_path.write_text(json.dumps(bad_config))

        # Temporarily override settings
        original = settings.DESIGNS_CONFIG
        settings.DESIGNS_CONFIG = bad_path
        try:
            designs = get_designs()
            print(f"  Designs loaded with bad config: {len(designs)}")
            # The ghost design should be excluded (file doesn't exist)
            ghost_ids = [d["id"] for d in designs if d["id"] == "GHOST"]
            assert len(ghost_ids) == 0, "Ghost design should be excluded"
        finally:
            settings.DESIGNS_CONFIG = original

    def test_zone_metadata_has_expected_fields(self):
        """Each zone has number, face_z, thickness, is_planar, faces_up, mode_options."""
        for design in get_designs():
            for zone in design["zones"]:
                print(f"  {design['id']} zone {zone['number']}: {zone}")
                assert "number" in zone
                assert "face_z" in zone
                assert "thickness" in zone
                assert "is_planar" in zone
                assert "faces_up" in zone
                assert "mode_options" in zone
                assert isinstance(zone["number"], int)
                assert isinstance(zone["thickness"], float)
                assert zone["thickness"] > 0, f"Zone {zone['number']} thickness <= 0"
