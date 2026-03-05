"""
Tests for image upload validation on the fingerprint preview API.

POST /api/preview/ accepts multipart/form-data with:
  - fingerprint: uploaded image file
  - design_id: string identifier (e.g. "PDG040")
  - zones: comma-separated ints (e.g. "1" or "1,2,3")
  - mode: "emboss" or "engrave"

These tests verify that the API correctly accepts valid image formats,
rejects invalid ones, and enforces size/content constraints.
"""

import io
import struct
import tempfile
import os

import numpy as np
import pytest
from PIL import Image

from preview.design_registry import _cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_design_cache():
    """Clear the design registry cache before every test."""
    _cache.clear()
    yield
    _cache.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_image_bytes(fmt="PNG", size=(64, 64), mode="L", content=None):
    """
    Generate an in-memory image file in the given format.

    Parameters
    ----------
    fmt : str
        PIL save format, e.g. "PNG", "JPEG", "BMP", "TIFF".
    size : tuple[int, int]
        Width x height.
    mode : str
        PIL image mode: "L" (grayscale), "RGB", "RGBA", etc.
    content : numpy.ndarray | None
        Optional pixel data. If None a random array is generated.

    Returns
    -------
    io.BytesIO
        Seeked-to-zero buffer containing the encoded image.
    """
    w, h = size
    if content is not None:
        img = Image.fromarray(content, mode=mode)
    else:
        if mode == "L":
            arr = np.random.randint(0, 256, (h, w), dtype=np.uint8)
        elif mode == "RGB":
            arr = np.random.randint(0, 256, (h, w, 3), dtype=np.uint8)
        elif mode == "RGBA":
            arr = np.random.randint(0, 256, (h, w, 4), dtype=np.uint8)
        else:
            arr = np.random.randint(0, 256, (h, w), dtype=np.uint8)
        img = Image.fromarray(arr, mode=mode)

    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    buf.name = f"test_image.{fmt.lower()}"
    return buf


def _post_fingerprint(api_client, file_obj, filename=None,
                      design_id="PDG040", zones="1", mode="emboss"):
    """
    POST to /api/preview/ with the given file and default form fields.

    Parameters
    ----------
    api_client : rest_framework.test.APIClient
    file_obj : file-like
        Must be opened / seeked to 0.
    filename : str | None
        Override the filename sent in the multipart payload.
    design_id : str
    zones : str
    mode : str

    Returns
    -------
    rest_framework.response.Response
    """
    if filename is not None:
        try:
            file_obj.name = filename
        except AttributeError:
            # BufferedReader doesn't allow setting name; wrap in SimpleUploadedFile
            from django.core.files.uploadedfile import SimpleUploadedFile
            file_obj.seek(0)
            content = file_obj.read()
            file_obj = SimpleUploadedFile(filename, content)

    return api_client.post(
        "/api/preview/",
        data={
            "fingerprint": file_obj,
            "design_id": design_id,
            "zones": zones,
            "mode": mode,
        },
        format="multipart",
    )


# ---------------------------------------------------------------------------
# Accepted formats
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAcceptedFormats:
    """Ensure the API accepts all required image formats."""

    def test_png_accepted(self, api_client):
        """PNG images must be accepted."""
        print("Uploading a valid 64x64 grayscale PNG ...")
        buf = _generate_image_bytes(fmt="PNG", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="fingerprint.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"PNG upload should be accepted, got {response.status_code}: "
            f"{response.data}"
        )

    def test_jpg_accepted(self, api_client):
        """JPG images must be accepted."""
        print("Uploading a valid 64x64 grayscale JPEG ...")
        buf = _generate_image_bytes(fmt="JPEG", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="fingerprint.jpg")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"JPG upload should be accepted, got {response.status_code}: "
            f"{response.data}"
        )

    def test_jpeg_extension_accepted(self, api_client):
        """Files with .jpeg extension must be accepted."""
        print("Uploading a valid 64x64 grayscale JPEG with .jpeg extension ...")
        buf = _generate_image_bytes(fmt="JPEG", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="fingerprint.jpeg")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"JPEG upload should be accepted, got {response.status_code}: "
            f"{response.data}"
        )

    def test_bmp_accepted(self, api_client):
        """BMP images must be accepted."""
        print("Uploading a valid 64x64 grayscale BMP ...")
        buf = _generate_image_bytes(fmt="BMP", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="fingerprint.bmp")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"BMP upload should be accepted, got {response.status_code}: "
            f"{response.data}"
        )

    def test_tiff_accepted(self, api_client):
        """TIFF images must be accepted."""
        print("Uploading a valid 64x64 grayscale TIFF ...")
        buf = _generate_image_bytes(fmt="TIFF", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="fingerprint.tiff")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"TIFF upload should be accepted, got {response.status_code}: "
            f"{response.data}"
        )


# ---------------------------------------------------------------------------
# Colour mode handling
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestColourModes:
    """Verify that different PIL colour modes are handled correctly."""

    def test_grayscale_accepted(self, api_client):
        """Grayscale (mode 'L') images must be accepted without conversion."""
        print("Uploading a grayscale (L) PNG ...")
        buf = _generate_image_bytes(fmt="PNG", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="gray.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"Grayscale image should be accepted, got {response.status_code}: "
            f"{response.data}"
        )

    def test_rgb_accepted_and_converted(self, api_client):
        """RGB images must be accepted (the pipeline converts to grayscale)."""
        print("Uploading an RGB PNG ...")
        buf = _generate_image_bytes(fmt="PNG", size=(64, 64), mode="RGB")
        response = _post_fingerprint(api_client, buf, filename="rgb.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"RGB image should be accepted and converted, got "
            f"{response.status_code}: {response.data}"
        )

    def test_rgba_accepted_and_converted(self, api_client):
        """RGBA images must be accepted (the pipeline strips alpha)."""
        print("Uploading an RGBA PNG ...")
        buf = _generate_image_bytes(fmt="PNG", size=(64, 64), mode="RGBA")
        response = _post_fingerprint(api_client, buf, filename="rgba.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"RGBA image should be accepted and converted, got "
            f"{response.status_code}: {response.data}"
        )


# ---------------------------------------------------------------------------
# Rejected formats
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestRejectedFormats:
    """Ensure the API rejects disallowed image formats."""

    def test_gif_rejected(self, api_client):
        """GIF images must be rejected with HTTP 400."""
        print("Uploading a GIF image (should be rejected) ...")
        buf = _generate_image_bytes(fmt="GIF", size=(64, 64), mode="L")
        response = _post_fingerprint(api_client, buf, filename="animation.gif")
        print(f"Response status: {response.status_code}")
        assert response.status_code == 400, (
            f"GIF upload should be rejected with 400, got {response.status_code}"
        )

    def test_svg_rejected(self, api_client):
        """SVG files must be rejected with HTTP 400."""
        print("Uploading an SVG file (should be rejected) ...")
        svg_content = (
            b'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
            b'<rect width="64" height="64" fill="black"/></svg>'
        )
        buf = io.BytesIO(svg_content)
        buf.name = "vector.svg"
        response = _post_fingerprint(api_client, buf, filename="vector.svg")
        print(f"Response status: {response.status_code}")
        assert response.status_code == 400, (
            f"SVG upload should be rejected with 400, got {response.status_code}"
        )


# ---------------------------------------------------------------------------
# Invalid / corrupt file content
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInvalidContent:
    """Verify the API rejects files with invalid or corrupt content."""

    def test_zero_byte_file_rejected(self, api_client):
        """An empty (zero-byte) file must be rejected with HTTP 400."""
        print("Uploading a zero-byte file (should be rejected) ...")
        buf = io.BytesIO(b"")
        buf.name = "empty.png"
        response = _post_fingerprint(api_client, buf, filename="empty.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code == 400, (
            f"Zero-byte file should be rejected with 400, got "
            f"{response.status_code}"
        )

    def test_non_image_with_png_extension_rejected(self, api_client):
        """
        A file that has a .png extension but is not actually a PNG
        (wrong magic bytes) must be rejected with HTTP 400.
        """
        print("Uploading a non-image file disguised as .png (should be rejected) ...")
        fake_content = b"This is definitely not a PNG image. Just plain text."
        buf = io.BytesIO(fake_content)
        buf.name = "fake.png"
        response = _post_fingerprint(api_client, buf, filename="fake.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code == 400, (
            f"Non-image with .png extension should be rejected with 400, got "
            f"{response.status_code}"
        )

    def test_truncated_image_rejected(self, api_client):
        """
        A file with a valid PNG header but a truncated body must be
        rejected with HTTP 400.
        """
        print("Uploading a truncated PNG (valid header, corrupt body) ...")
        # Build a minimal PNG signature + IHDR, then cut off abruptly.
        png_signature = b"\x89PNG\r\n\x1a\n"
        # IHDR chunk: length(13) + "IHDR" + width(4) + height(4) + bit depth
        # + colour type + compression + filter + interlace + CRC
        ihdr_data = struct.pack(">II", 64, 64) + b"\x08\x00\x00\x00\x00"
        ihdr_crc = b"\x00\x00\x00\x00"  # deliberately wrong CRC
        ihdr_chunk = (
            struct.pack(">I", 13) + b"IHDR" + ihdr_data + ihdr_crc
        )
        # Truncate: no IDAT, no IEND
        truncated_png = png_signature + ihdr_chunk
        buf = io.BytesIO(truncated_png)
        buf.name = "truncated.png"
        response = _post_fingerprint(api_client, buf, filename="truncated.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code == 400, (
            f"Truncated PNG should be rejected with 400, got "
            f"{response.status_code}"
        )


# ---------------------------------------------------------------------------
# Size constraints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSizeConstraints:
    """Verify image size limits are enforced."""

    def test_image_over_10mb_rejected(self, api_client):
        """
        An image whose file size exceeds 10 MB must be rejected
        with HTTP 400.
        """
        print("Generating an image larger than 10 MB ...")
        # Create a large uncompressed BMP to guarantee > 10 MB on disk.
        # A 2000x2000 RGB BMP is ~12 MB.
        large_size = (2000, 2000)
        arr = np.random.randint(0, 256, (large_size[1], large_size[0], 3),
                                dtype=np.uint8)
        img = Image.fromarray(arr, "RGB")

        # Write to a temporary file so we can check actual size.
        tmp = tempfile.NamedTemporaryFile(suffix=".bmp", delete=False)
        try:
            img.save(tmp, format="BMP")
            tmp.flush()
            file_size = os.path.getsize(tmp.name)
            print(f"Generated BMP file size: {file_size / (1024 * 1024):.2f} MB")

            # If the file isn't big enough, pad it.
            if file_size <= 10 * 1024 * 1024:
                with open(tmp.name, "ab") as f:
                    padding = (10 * 1024 * 1024 + 1) - file_size
                    f.write(b"\x00" * padding)
                file_size = os.path.getsize(tmp.name)
                print(f"Padded file size: {file_size / (1024 * 1024):.2f} MB")

            assert file_size > 10 * 1024 * 1024, "Test image must exceed 10 MB"

            with open(tmp.name, "rb") as f:
                response = _post_fingerprint(api_client, f, filename="huge.bmp")
            print(f"Response status: {response.status_code}")
            assert response.status_code == 400, (
                f"Image >10 MB should be rejected with 400, got "
                f"{response.status_code}"
            )
        finally:
            os.unlink(tmp.name)

    def test_very_small_image_accepted(self, api_client):
        """A tiny 1x1 pixel image must still be accepted."""
        print("Uploading a 1x1 pixel PNG ...")
        buf = _generate_image_bytes(fmt="PNG", size=(1, 1), mode="L")
        response = _post_fingerprint(api_client, buf, filename="tiny.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"1x1 pixel image should be accepted, got {response.status_code}: "
            f"{response.data}"
        )

    def test_very_large_dimensions_accepted(self, api_client):
        """
        An image with large pixel dimensions should still be accepted
        because the pipeline downsamples before processing.
        Use a solid-color image to keep file size well under 10MB.
        """
        print("Uploading a 2000x2000 grayscale PNG (large dimensions) ...")
        # Solid gray compresses very small in PNG
        arr = np.full((2000, 2000), 128, dtype=np.uint8)
        img = Image.fromarray(arr, "L")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "large_dimensions.png"
        file_size = buf.getbuffer().nbytes
        print(f"Large-dimension PNG file size: {file_size / (1024 * 1024):.2f} MB")

        response = _post_fingerprint(api_client, buf, filename="large_dimensions.png")
        print(f"Response status: {response.status_code}")
        assert response.status_code != 400, (
            f"Large-dimension image should be accepted (pipeline downsamples), "
            f"got {response.status_code}: {response.data}"
        )
