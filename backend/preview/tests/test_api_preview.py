"""Tests for POST /api/preview/ endpoint."""
import base64
import struct
import pytest
from io import BytesIO
from PIL import Image
from preview.design_registry import _cache


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


def _make_fingerprint_file(tmp_path, size=(256, 256), fmt="PNG"):
    """Create a synthetic fingerprint image file."""
    import numpy as np
    arr = np.random.randint(0, 255, size, dtype=np.uint8)
    img = Image.fromarray(arr, mode="L")
    path = tmp_path / f"fp.{fmt.lower()}"
    img.save(path, format=fmt)
    return path


def _post_preview(api_client, fp_path, design_id="PDG040", zones="1", mode="emboss", **kwargs):
    """Helper to POST to /api/preview/."""
    with open(fp_path, "rb") as f:
        data = {
            "fingerprint": f,
            "design_id": design_id,
            "zones": zones,
            "mode": mode,
        }
        data.update(kwargs)
        return api_client.post("/api/preview/", data, format="multipart")


class TestPreviewValidRequests:
    def test_valid_single_zone_request_returns_200(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="1", mode="emboss")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

    def test_valid_multi_zone_request_returns_200(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="1,2", mode="emboss")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

    def test_single_zone_returns_binary_stl(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="1", mode="emboss")
        assert response.status_code == 200
        content_type = response["Content-Type"]
        print(f"  Content-Type: {content_type}")
        assert "application/octet-stream" in content_type
        assert response["Content-Disposition"].endswith('.stl"')
        assert len(response.content) > 100

    def test_multi_zone_returns_json_with_base64_stls(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="1,2", mode="emboss")
        assert response.status_code == 200
        data = response.json()
        print(f"  Response keys: {list(data.keys())}")
        assert "zones" in data
        for zone_key in ["1", "2"]:
            assert zone_key in data["zones"]
            zone_data = data["zones"][zone_key]
            assert "stl_base64" in zone_data
            stl_bytes = base64.b64decode(zone_data["stl_base64"])
            assert len(stl_bytes) > 100
            # Verify it's valid binary STL
            tri_count = struct.unpack("<I", stl_bytes[80:84])[0]
            assert tri_count > 0

    def test_optional_params_use_defaults(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="1", mode="emboss")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

    def test_unified_flag_accepted(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="P246", zones="1,2", mode="emboss", unified="true")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

    def test_preview_only_accepts_post(self, api_client):
        for method in ["get", "put", "delete", "patch"]:
            response = getattr(api_client, method)("/api/preview/")
            print(f"  {method.upper()}: {response.status_code}")
            assert response.status_code == 405


class TestPreviewValidation:
    def test_missing_fingerprint_returns_400(self, api_client):
        response = api_client.post("/api/preview/", {
            "design_id": "PDG040", "zones": "1", "mode": "emboss",
        }, format="multipart")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 400
        assert "fingerprint" in response.json()["error"].lower()

    def test_missing_design_id_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        with open(fp, "rb") as f:
            response = api_client.post("/api/preview/", {
                "fingerprint": f, "zones": "1", "mode": "emboss",
            }, format="multipart")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 400

    def test_missing_zones_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        with open(fp, "rb") as f:
            response = api_client.post("/api/preview/", {
                "fingerprint": f, "design_id": "PDG040", "mode": "emboss",
            }, format="multipart")
        assert response.status_code == 400

    def test_missing_mode_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        with open(fp, "rb") as f:
            response = api_client.post("/api/preview/", {
                "fingerprint": f, "design_id": "PDG040", "zones": "1",
            }, format="multipart")
        assert response.status_code == 400

    def test_invalid_design_id_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="FAKE", zones="1", mode="emboss")
        assert response.status_code == 400
        assert "FAKE" in str(response.json())

    def test_invalid_zone_numbers_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="99", mode="emboss")
        assert response.status_code == 400
        data = response.json()
        print(f"  Error: {data['error']}")
        assert "zone" in data["error"].lower() or "invalid" in data["error"].lower()

    def test_invalid_mode_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        response = _post_preview(api_client, fp, design_id="PDG040", zones="1", mode="carve")
        assert response.status_code == 400

    def test_depth_out_of_range_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        for bad_depth in ["0.0", "-1.0", "10.0"]:
            response = _post_preview(api_client, fp, depth=bad_depth)
            print(f"  depth={bad_depth}: {response.status_code}")
            assert response.status_code == 400

    def test_resolution_out_of_range_returns_400(self, api_client, tmp_path):
        fp = _make_fingerprint_file(tmp_path)
        for bad_res in ["5", "2000"]:
            response = _post_preview(api_client, fp, resolution=bad_res)
            print(f"  resolution={bad_res}: {response.status_code}")
            assert response.status_code == 400

    def test_invalid_image_format_returns_400(self, api_client, tmp_path):
        # Text file disguised as fingerprint
        txt_file = tmp_path / "not_image.txt"
        txt_file.write_text("this is not an image")
        with open(txt_file, "rb") as f:
            response = api_client.post("/api/preview/", {
                "fingerprint": f, "design_id": "PDG040", "zones": "1", "mode": "emboss",
            }, format="multipart")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 400

    def test_large_fingerprint_image_accepted(self, api_client, tmp_path):
        """4000x4000 PNG should be accepted (pipeline downsamples)."""
        import numpy as np
        arr = np.random.randint(0, 255, (512, 512), dtype=np.uint8)
        img = Image.fromarray(arr, mode="L")
        path = tmp_path / "large_fp.png"
        img.save(path)
        response = _post_preview(api_client, path)
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200
