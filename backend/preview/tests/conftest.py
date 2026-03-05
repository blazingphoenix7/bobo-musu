"""Shared fixtures and configuration for all tests."""
import pytest
from pathlib import Path
from django.conf import settings

DESIGNS = ["PDG040", "P246"]
MODES = ["emboss", "engrave"]


def _build_combo_matrix():
    """Build test combos from actual design files."""
    from preview.design_registry import get_designs
    combos = []
    for design in get_designs():
        for zone in design["zones"]:
            zone_num = zone["number"] if isinstance(zone, dict) else zone
            for mode in MODES:
                combos.append((design["id"], zone_num, mode))
    return combos


def _get_all_combos():
    try:
        return _build_combo_matrix()
    except Exception:
        return []


ALL_COMBOS = _get_all_combos()


def combo_id(combo):
    """Human-readable test ID: 'PDG040-Z1-emboss'"""
    return f"{combo[0]}-Z{combo[1]}-{combo[2]}"


@pytest.fixture
def api_client():
    """DRF test client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def sample_fingerprint(tmp_path):
    """Generate a synthetic fingerprint image for testing."""
    from PIL import Image
    import numpy as np
    img_array = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
    img = Image.fromarray(img_array, mode="L")
    path = tmp_path / "test_fingerprint.png"
    img.save(path)
    return path


@pytest.fixture
def synthetic_fingerprint(tmp_path):
    """Generate the same synthetic fingerprint as the pipeline's --test mode."""
    import sys
    sys.path.insert(0, str(settings.BASE_DIR.parent / "3dm files"))
    from fingerprint_displace import generate_test_fingerprint
    path = str(tmp_path / "synthetic_fp.png")
    generate_test_fingerprint(path)
    return Path(path)


@pytest.fixture
def all_combos():
    """Return the full parametric matrix."""
    return ALL_COMBOS
