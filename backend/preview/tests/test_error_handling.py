"""
Test error handling for the fingerprint preview API.

Ensures that:
  - Error responses never leak internal filesystem paths.
  - Every error response is valid JSON with an ``"error"`` key.
  - Oversized uploads are rejected before any heavy processing.
  - Malformed multipart bodies produce 400, not 500.
"""

import io
import json

import numpy as np
import pytest
from PIL import Image

from preview.pipeline import generate_preview_stl, PipelineError
from preview.design_registry import get_design_path, _cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_design_cache():
    """Clear the design registry cache before every test."""
    _cache.clear()
    yield
    _cache.clear()


# Paths that should never appear in user-facing responses.
_LEAKED_PATH_FRAGMENTS = ("/Users/", "/home/", "/tmp/", "\\Users\\", "\\home\\")


def _response_body_text(response) -> str:
    """Return the decoded response body as a string."""
    return response.content.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Tests – path leakage
# ---------------------------------------------------------------------------


class TestNoPathLeakage:
    """API errors must never expose internal filesystem paths."""

    def test_api_errors_never_leak_filesystem_paths_missing_file(self, api_client):
        """POST with missing fingerprint file must not reveal server paths."""
        response = api_client.post(
            "/api/preview/",
            data={"design_id": "PDG040", "zones": "1", "mode": "emboss"},
            format="multipart",
        )

        body = _response_body_text(response)
        print(f"Status: {response.status_code}")
        print(f"Body:   {body[:500]}")

        for fragment in _LEAKED_PATH_FRAGMENTS:
            assert fragment not in body, (
                f"Response leaked filesystem path fragment '{fragment}': {body[:300]}"
            )

    def test_api_errors_never_leak_filesystem_paths_bad_design(
        self, api_client, synthetic_fingerprint
    ):
        """POST with a non-existent design_id must not reveal server paths."""
        fp_bytes = open(synthetic_fingerprint, "rb").read()
        fp_file = io.BytesIO(fp_bytes)
        fp_file.name = "fingerprint.png"

        response = api_client.post(
            "/api/preview/",
            data={
                "fingerprint": fp_file,
                "design_id": "DOESNOTEXIST999",
                "zones": "1",
                "mode": "emboss",
            },
            format="multipart",
        )

        body = _response_body_text(response)
        print(f"Status: {response.status_code}")
        print(f"Body:   {body[:500]}")

        for fragment in _LEAKED_PATH_FRAGMENTS:
            assert fragment not in body, (
                f"Response leaked filesystem path fragment '{fragment}': {body[:300]}"
            )


# ---------------------------------------------------------------------------
# Tests – JSON shape
# ---------------------------------------------------------------------------


class TestErrorResponseFormat:
    """Every error response must be parseable JSON containing an 'error' key."""

    @pytest.mark.parametrize(
        "payload,description",
        [
            ({}, "completely empty payload"),
            ({"design_id": "PDG040"}, "missing fingerprint and zones"),
            ({"zones": "1", "mode": "emboss"}, "missing fingerprint and design_id"),
        ],
        ids=["empty", "no-file-no-zones", "no-file-no-design"],
    )
    def test_api_errors_are_json(self, api_client, payload, description):
        """Error response for '{description}' must be JSON with 'error' key."""
        response = api_client.post("/api/preview/", data=payload, format="multipart")

        body_text = _response_body_text(response)
        print(f"[{description}] Status: {response.status_code}")
        print(f"[{description}] Body:   {body_text[:500]}")

        assert response.status_code >= 400, (
            f"Expected an error status code but got {response.status_code}"
        )

        try:
            body_json = json.loads(body_text)
        except json.JSONDecodeError:
            pytest.fail(
                f"Response body is not valid JSON for '{description}': {body_text[:300]}"
            )

        assert "error" in body_json, (
            f"JSON response missing 'error' key for '{description}': {body_json}"
        )
        print(f"[{description}] error value: {body_json['error']}")


# ---------------------------------------------------------------------------
# Tests – oversized upload
# ---------------------------------------------------------------------------


class TestOversizedUpload:
    """Uploads exceeding the size limit must be rejected immediately."""

    def test_oversized_upload_rejected_before_processing(self, api_client):
        """A >10 MB PNG upload must receive a 400 response."""
        # Build a genuinely large PNG: ~3500x3500 RGBA ≈ ~49 MB raw;
        # even after PNG compression this will exceed 10 MB.
        print("Generating oversized image (~3500x3500 RGBA) ...")
        rng = np.random.default_rng(seed=42)
        large_array = rng.integers(0, 256, (3500, 3500, 4), dtype=np.uint8)
        img = Image.fromarray(large_array, mode="RGBA")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        size_mb = buf.getbuffer().nbytes / (1024 * 1024)
        print(f"PNG size: {size_mb:.2f} MB")

        # If compression made it under 10 MB, pad with random bytes inside a
        # new BytesIO to guarantee the threshold is crossed.
        if size_mb < 10.5:
            print("PNG compressed below 10 MB – padding to exceed limit ...")
            extra = b"\x00" * (11 * 1024 * 1024 - buf.getbuffer().nbytes)
            raw = buf.getvalue() + extra
            buf = io.BytesIO(raw)
            buf.name = "oversized.png"
            print(f"Padded size: {len(buf.getvalue()) / (1024 * 1024):.2f} MB")

        buf.name = "oversized.png"

        response = api_client.post(
            "/api/preview/",
            data={
                "fingerprint": buf,
                "design_id": "PDG040",
                "zones": "1",
                "mode": "emboss",
            },
            format="multipart",
        )

        print(f"Status: {response.status_code}")
        print(f"Body:   {_response_body_text(response)[:500]}")

        assert response.status_code == 400, (
            f"Expected 400 for oversized upload but got {response.status_code}"
        )


# ---------------------------------------------------------------------------
# Tests – malformed multipart
# ---------------------------------------------------------------------------


class TestMalformedMultipart:
    """Broken multipart bodies must result in 400 Bad Request, not 500."""

    def test_malformed_multipart_returns_400(self, api_client):
        """Sending raw garbage as the body with a multipart content type
        must return 400, never 500."""
        response = api_client.post(
            "/api/preview/",
            data=b"THIS-IS-NOT-VALID-MULTIPART",
            content_type="multipart/form-data; boundary=garbage",
        )

        body = _response_body_text(response)
        print(f"Status: {response.status_code}")
        print(f"Body:   {body[:500]}")

        assert response.status_code == 400, (
            f"Expected 400 for malformed multipart but got {response.status_code}"
        )
        assert response.status_code != 500, (
            "Malformed multipart must not cause an Internal Server Error (500)"
        )
