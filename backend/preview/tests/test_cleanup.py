"""Temp-file cleanup tests for the fingerprint preview pipeline."""
import os
import shutil
import pytest
from django.conf import settings

from preview.pipeline import generate_preview_stl, PipelineError
from preview.design_registry import get_design_path, _cache


@pytest.fixture(autouse=True)
def clear_design_cache():
    _cache.clear()
    yield
    _cache.clear()


def _count_files(directory):
    """Return number of files inside directory, or 0 if it doesn't exist."""
    if not os.path.isdir(str(directory)):
        return 0
    return sum(len(files) for _, _, files in os.walk(str(directory)))


class TestSuccessfulRequestCleanup:
    def test_successful_request_leaves_no_temp_files(self, synthetic_fingerprint):
        """Count files in temp dir before and after a successful run."""
        temp_dir = settings.PREVIEW_TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        before = _count_files(temp_dir)
        print(f"  Files BEFORE: {before}")

        design_path = get_design_path("PDG040")
        result = generate_preview_stl(
            design_path=design_path,
            fingerprint_file=synthetic_fingerprint,
            zones=[1],
            mode="emboss",
            resolution=80,
        )
        print(f"  Pipeline returned {len(result)} zone(s)")

        after = _count_files(temp_dir)
        print(f"  Files AFTER: {after}")
        assert after <= before, f"Temp files leaked: {after - before} new files"


class TestFailedRequestCleanup:
    def test_failed_request_leaves_no_temp_files(self, tmp_path):
        """Trigger failure and verify cleanup."""
        bad_file = tmp_path / "not_an_image.txt"
        bad_file.write_text("this is not a PNG")

        temp_dir = settings.PREVIEW_TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        before = _count_files(temp_dir)
        print(f"  Files BEFORE: {before}")

        design_path = get_design_path("PDG040")
        try:
            generate_preview_stl(
                design_path=design_path,
                fingerprint_file=bad_file,
                zones=[1],
                mode="emboss",
                resolution=80,
            )
        except (PipelineError, Exception) as exc:
            print(f"  Pipeline raised {type(exc).__name__}: {exc}")

        after = _count_files(temp_dir)
        print(f"  Files AFTER: {after}")
        assert after <= before, f"Temp files leaked: {after - before} new files"


class TestTempDirRecreation:
    def test_temp_dir_is_created_if_missing(self, synthetic_fingerprint):
        """Delete temp dir, run pipeline, assert succeeds."""
        temp_dir = settings.PREVIEW_TEMP_DIR
        if temp_dir.exists():
            shutil.rmtree(str(temp_dir))
            print(f"  Removed temp dir: {temp_dir}")

        design_path = get_design_path("PDG040")
        result = generate_preview_stl(
            design_path=design_path,
            fingerprint_file=synthetic_fingerprint,
            zones=[1],
            mode="emboss",
            resolution=80,
        )
        assert isinstance(result, dict)
        assert 1 in result
        assert len(result[1]) > 100
        print(f"  Pipeline returned {len(result[1])} bytes after temp dir removal")
