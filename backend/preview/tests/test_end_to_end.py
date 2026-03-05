"""End-to-end tests: full user flow through the API."""
import base64
import struct
import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from preview.design_registry import _cache


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


def _make_fp(tmp_path, seed=42):
    """Create a fingerprint image with a specific seed."""
    rng = np.random.RandomState(seed)
    arr = rng.randint(0, 255, (256, 256), dtype=np.uint8)
    img = Image.fromarray(arr, mode="L")
    path = tmp_path / f"fp_{seed}.png"
    img.save(path)
    return path


def _post_preview(client, fp_path, design_id, zones, mode, **kwargs):
    with open(fp_path, "rb") as f:
        data = {"fingerprint": f, "design_id": design_id, "zones": zones, "mode": mode}
        data.update(kwargs)
        return client.post("/api/preview/", data, format="multipart")


def _parse_stl_tri_count(stl_bytes):
    return struct.unpack("<I", stl_bytes[80:84])[0]


class TestEndToEnd:
    def test_full_flow_single_zone(self, api_client, tmp_path):
        """1. List designs -> 2. Get detail -> 3. Preview zone 1 -> 4. Validate STL."""
        # Step 1: list designs
        resp = api_client.get("/api/designs/")
        assert resp.status_code == 200
        designs = resp.json()["designs"]
        assert len(designs) >= 1
        design = designs[0]
        print(f"  Step 1: Found {len(designs)} designs, using {design['id']}")

        # Step 2: get detail
        resp = api_client.get(f"/api/designs/{design['id']}/")
        assert resp.status_code == 200
        detail = resp.json()
        zones = [z["number"] for z in detail["zones"]]
        print(f"  Step 2: Zones = {zones}")

        # Step 3: preview
        fp = _make_fp(tmp_path)
        resp = _post_preview(api_client, fp, design["id"], str(zones[0]), "emboss")
        assert resp.status_code == 200
        print(f"  Step 3: Preview returned {len(resp.content)} bytes")

        # Step 4: validate
        tri_count = _parse_stl_tri_count(resp.content)
        print(f"  Step 4: {tri_count} triangles")
        assert tri_count > 0

    def test_full_flow_multi_zone(self, api_client, tmp_path):
        """Multi-zone preview returns all zones."""
        fp = _make_fp(tmp_path)
        resp = _post_preview(api_client, fp, "PDG040", "1,2", "emboss")
        assert resp.status_code == 200
        data = resp.json()
        assert "zones" in data
        for zkey in ["1", "2"]:
            stl_bytes = base64.b64decode(data["zones"][zkey]["stl_base64"])
            tri = _parse_stl_tri_count(stl_bytes)
            print(f"  Zone {zkey}: {tri} triangles")
            assert tri > 0

    def test_full_flow_all_modes(self, api_client, tmp_path):
        """Emboss and engrave both valid and different."""
        fp = _make_fp(tmp_path)
        r_emb = _post_preview(api_client, fp, "PDG040", "1", "emboss")
        r_eng = _post_preview(api_client, fp, "PDG040", "1", "engrave")
        assert r_emb.status_code == 200
        assert r_eng.status_code == 200
        assert r_emb.content != r_eng.content
        print(f"  Emboss: {len(r_emb.content)} bytes, Engrave: {len(r_eng.content)} bytes")

    def test_full_flow_unified(self, api_client, tmp_path):
        """PDG040 all 5 zones unified."""
        fp = _make_fp(tmp_path)
        resp = _post_preview(api_client, fp, "PDG040", "1,2,3,4,5", "emboss", unified="true")
        assert resp.status_code == 200
        data = resp.json()
        print(f"  Zones returned: {list(data['zones'].keys())}")
        assert len(data["zones"]) == 5

    def test_full_flow_with_real_fingerprint_image(self, api_client):
        """Use the actual test fingerprint from 3dm files/fingerprints/."""
        from django.conf import settings
        fp_path = settings.BASE_DIR.parent / "3dm files" / "fingerprints" / "fingerprint_preprocessed.png"
        if not fp_path.exists():
            pytest.skip("Real fingerprint image not found")
        resp = _post_preview(api_client, fp_path, "PDG040", "1", "emboss")
        print(f"  Status: {resp.status_code}")
        assert resp.status_code == 200
        assert len(resp.content) > 100

    def test_preview_then_different_design(self, api_client, tmp_path):
        """Preview PDG040 then P246, both valid and different."""
        fp = _make_fp(tmp_path)
        r1 = _post_preview(api_client, fp, "PDG040", "1", "emboss")
        r2 = _post_preview(api_client, fp, "P246", "1", "emboss")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.content != r2.content
        print(f"  PDG040: {len(r1.content)} bytes, P246: {len(r2.content)} bytes")

    def test_preview_then_different_fingerprint(self, api_client, tmp_path):
        """Same design/zone/mode but different fingerprints -> different STL."""
        fp_a = _make_fp(tmp_path, seed=1)
        fp_b = _make_fp(tmp_path, seed=999)
        r1 = _post_preview(api_client, fp_a, "PDG040", "1", "emboss")
        r2 = _post_preview(api_client, fp_b, "PDG040", "1", "emboss")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.content != r2.content
        print(f"  FP-A: {len(r1.content)} bytes, FP-B: {len(r2.content)} bytes")

    def test_stl_loadable_by_three_js_stl_loader(self, api_client, tmp_path):
        """Parse STL bytes the same way three.js does."""
        fp = _make_fp(tmp_path)
        resp = _post_preview(api_client, fp, "PDG040", "1", "emboss")
        assert resp.status_code == 200
        data = resp.content

        # Parse like three.js STLLoader (binary)
        assert len(data) >= 84
        header = data[:80]
        tri_count = struct.unpack("<I", data[80:84])[0]
        print(f"  Header: {len(header)} bytes")
        print(f"  Triangles: {tri_count}")
        assert tri_count > 0

        vertices = []
        offset = 84
        for _ in range(tri_count):
            assert offset + 50 <= len(data)
            # Skip normal (12 bytes)
            # Read 3 vertices (36 bytes)
            for v in range(3):
                voff = offset + 12 + v * 12
                x, y, z = struct.unpack("<fff", data[voff:voff + 12])
                assert not (x != x or y != y or z != z), "NaN detected"
                vertices.append((x, y, z))
            offset += 50

        print(f"  Vertex array: {len(vertices)} vertices")
        assert len(vertices) == tri_count * 3
        assert len(vertices) > 0
