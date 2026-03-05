"""Frontend smoke tests: verify the index page and static files load."""
import pytest
from preview.design_registry import _cache


@pytest.fixture(autouse=True)
def clear_cache():
    _cache.clear()
    yield
    _cache.clear()


class TestFrontendSmoke:
    def test_index_page_returns_200(self, api_client):
        response = api_client.get("/")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

    def test_index_page_contains_required_elements(self, api_client):
        response = api_client.get("/")
        html = response.content.decode()
        required = [
            'type="file"',
            "design-select",
            'name="mode"',
            "generate-btn",
            "viewer-canvas",
        ]
        for elem in required:
            print(f"  Checking for: {elem}")
            assert elem in html, f"Missing element: {elem}"

    def test_static_files_exist(self):
        """Verify static files exist on disk."""
        from django.conf import settings
        static_dir = settings.STATICFILES_DIRS[0]
        for filename in ["app.js", "style.css"]:
            path = static_dir / filename
            print(f"  {filename}: exists={path.exists()}")
            assert path.exists(), f"Static file not found: {path}"

    def test_three_js_cdn_url_in_page(self, api_client):
        response = api_client.get("/")
        html = response.content.decode()
        assert "three@0.170.0" in html, "three.js CDN import not found"
        print("  three.js CDN URL found in page")
