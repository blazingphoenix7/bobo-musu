"""Shared fixtures for fingerprint_displace tests."""
import os
import sys
import pytest

# Add parent directory to path so we can import fingerprint_displace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rhino3dm
from fingerprint_displace import generate_test_fingerprint, preprocess_fingerprint


DESIGNS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "designs")
FINGERPRINTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fingerprints")


@pytest.fixture(scope="session")
def pdg040_model():
    """Load the PDG040 design (5 zones, FP_ZONE convention)."""
    path = os.path.join(DESIGNS_DIR, "PDG040.3dm")
    if not os.path.isfile(path):
        pytest.skip(f"Design file not found: {path}")
    model = rhino3dm.File3dm.Read(path)
    assert model is not None
    return model


@pytest.fixture(scope="session")
def p246_model():
    """Load the P246442LY design (2 zones, FP_ZONE convention)."""
    path = os.path.join(DESIGNS_DIR, "P246442LY.3dm")
    if not os.path.isfile(path):
        pytest.skip(f"Design file not found: {path}")
    model = rhino3dm.File3dm.Read(path)
    assert model is not None
    return model


@pytest.fixture(scope="session")
def aap_model():
    """Load the AAP10985F design (3 zones, may use TextDot labels)."""
    path = os.path.join(DESIGNS_DIR, "AAP10985F.3dm")
    if not os.path.isfile(path):
        pytest.skip(f"Design file not found: {path}")
    model = rhino3dm.File3dm.Read(path)
    assert model is not None
    return model


@pytest.fixture(scope="session")
def test_fingerprint_img(tmp_path_factory):
    """Generate a synthetic test fingerprint image."""
    fp_dir = tmp_path_factory.mktemp("fingerprints")
    fp_path = str(fp_dir / "test_fp.png")
    generate_test_fingerprint(fp_path, size=256)
    return preprocess_fingerprint(fp_path, target_size=256)


@pytest.fixture(scope="session")
def real_fingerprint_img():
    """Load the real test fingerprint if available."""
    path = os.path.join(FINGERPRINTS_DIR, "test_fingerprint.png")
    if not os.path.isfile(path):
        pytest.skip(f"Test fingerprint not found: {path}")
    return preprocess_fingerprint(path, target_size=512)


@pytest.fixture(scope="session")
def synthetic_fingerprint(tmp_path_factory):
    """Generate a synthetic fingerprint image for edge-case tests."""
    fp_dir = tmp_path_factory.mktemp("synthetic_fp")
    fp_path = str(fp_dir / "synthetic_fp.png")
    generate_test_fingerprint(fp_path, size=256)
    return preprocess_fingerprint(fp_path, target_size=256)
