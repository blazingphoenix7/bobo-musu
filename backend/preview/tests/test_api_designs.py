"""Tests for GET /api/designs/ and GET /api/designs/{id}/ endpoints."""
import pytest
from preview.design_registry import _cache


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


class TestDesignListEndpoint:
    def test_list_designs_returns_200(self, api_client):
        response = api_client.get("/api/designs/")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

    def test_list_designs_response_structure(self, api_client):
        response = api_client.get("/api/designs/")
        data = response.json()
        assert "designs" in data
        for design in data["designs"]:
            print(f"  Design: {design['id']}")
            assert "id" in design
            assert "display_name" in design
            assert "description" in design
            assert "zones" in design
            assert isinstance(design["zones"], list)
            assert len(design["zones"]) > 0
            for z in design["zones"]:
                assert isinstance(z, int)

    def test_list_designs_contains_all_known_designs(self, api_client):
        response = api_client.get("/api/designs/")
        data = response.json()
        ids = [d["id"] for d in data["designs"]]
        print(f"  Design IDs: {ids}")
        assert "PDG040" in ids, "PDG040 missing from designs list"
        assert "P246" in ids, "P246 missing from designs list"

    def test_designs_endpoint_is_idempotent(self, api_client):
        r1 = api_client.get("/api/designs/")
        r2 = api_client.get("/api/designs/")
        assert r1.json() == r2.json(), "Responses should be identical"

    def test_designs_endpoint_allows_only_get(self, api_client):
        for method in ["post", "put", "delete", "patch"]:
            response = getattr(api_client, method)("/api/designs/")
            print(f"  {method.upper()}: {response.status_code}")
            assert response.status_code == 405, (
                f"{method.upper()} should return 405, got {response.status_code}"
            )

    def test_content_type_is_json(self, api_client):
        response = api_client.get("/api/designs/")
        content_type = response["Content-Type"]
        print(f"  Content-Type: {content_type}")
        assert "application/json" in content_type


class TestDesignDetailEndpoint:
    def test_design_detail_returns_200_for_valid_id(self, api_client):
        for design_id in ["PDG040", "P246"]:
            response = api_client.get(f"/api/designs/{design_id}/")
            print(f"  {design_id}: {response.status_code}")
            assert response.status_code == 200

    def test_design_detail_response_structure(self, api_client):
        response = api_client.get("/api/designs/PDG040/")
        data = response.json()
        print(f"  Response keys: {list(data.keys())}")
        assert "id" in data
        assert "display_name" in data
        assert "description" in data
        assert "zones" in data
        assert isinstance(data["zones"], list)
        for zone in data["zones"]:
            assert "number" in zone
            assert "is_planar" in zone
            assert "faces_up" in zone

    def test_design_detail_returns_404_for_invalid_id(self, api_client):
        response = api_client.get("/api/designs/NONEXISTENT/")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    def test_design_detail_zone_count_matches_list(self, api_client):
        list_response = api_client.get("/api/designs/")
        for design in list_response.json()["designs"]:
            detail_response = api_client.get(f"/api/designs/{design['id']}/")
            detail_zones = [z["number"] for z in detail_response.json()["zones"]]
            print(f"  {design['id']}: list={design['zones']}, detail={detail_zones}")
            assert design["zones"] == detail_zones, (
                f"Zone count mismatch for {design['id']}"
            )

    def test_detail_endpoint_allows_only_get(self, api_client):
        for method in ["post", "put", "delete", "patch"]:
            response = getattr(api_client, method)("/api/designs/PDG040/")
            print(f"  {method.upper()}: {response.status_code}")
            assert response.status_code == 405

    def test_detail_content_type_is_json(self, api_client):
        response = api_client.get("/api/designs/PDG040/")
        content_type = response["Content-Type"]
        print(f"  Content-Type: {content_type}")
        assert "application/json" in content_type
