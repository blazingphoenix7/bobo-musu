"""
Concurrency tests for the fingerprint preview pipeline.

Uses ``concurrent.futures.ThreadPoolExecutor`` to run multiple pipeline
calls in parallel and verify correctness under concurrent load.
"""

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

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


def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConcurrentDifferentDesigns:
    """Two different designs processed at the same time must both succeed
    and produce distinct output."""

    def test_two_different_designs_concurrent(self, synthetic_fingerprint):
        """PDG040-Z1 and P246-Z1 concurrently – both valid, both different."""
        configs = [
            {"design_id": "PDG040", "zone": 1, "label": "PDG040-Z1"},
            {"design_id": "P246", "zone": 1, "label": "P246-Z1"},
        ]

        def _run(cfg):
            print(f"[{cfg['label']}] Starting ...")
            result = generate_preview_stl(
                design_path=get_design_path(cfg["design_id"]),
                fingerprint_file=synthetic_fingerprint,
                zones=[cfg["zone"]],
                mode="emboss",
                resolution=80,
            )
            stl_bytes = result[cfg["zone"]]
            digest = _md5(stl_bytes)
            print(f"[{cfg['label']}] Done – {len(stl_bytes)} bytes, MD5={digest}")
            return cfg["label"], stl_bytes, digest

        results = {}
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {pool.submit(_run, c): c["label"] for c in configs}
            for future in as_completed(futures):
                label, data, digest = future.result()
                results[label] = (data, digest)

        assert len(results) == 2, "Expected 2 results from concurrent runs"

        labels = list(results.keys())
        d0 = results[labels[0]][1]
        d1 = results[labels[1]][1]

        print(f"\n{labels[0]} MD5: {d0}")
        print(f"{labels[1]} MD5: {d1}")

        assert d0 != d1, (
            "Two different designs should produce different STL output even "
            "when processed concurrently"
        )


class TestConcurrentIdenticalRequests:
    """Identical requests processed concurrently must all return the
    same byte-identical result (determinism under concurrency)."""

    def test_same_request_concurrent(self, synthetic_fingerprint):
        """3 identical requests concurrently – all byte-identical."""
        N = 3

        def _run(idx):
            print(f"[Worker {idx}] Starting ...")
            result = generate_preview_stl(
                design_path=get_design_path("PDG040"),
                fingerprint_file=synthetic_fingerprint,
                zones=[1],
                mode="emboss",
                resolution=80,
            )
            stl_bytes = result[1]
            digest = _md5(stl_bytes)
            print(f"[Worker {idx}] Done – {len(stl_bytes)} bytes, MD5={digest}")
            return idx, stl_bytes, digest

        results = {}
        with ThreadPoolExecutor(max_workers=N) as pool:
            futures = [pool.submit(_run, i) for i in range(N)]
            for future in as_completed(futures):
                idx, data, digest = future.result()
                results[idx] = (data, digest)

        digests = [results[i][1] for i in range(N)]
        for i, d in enumerate(digests):
            print(f"Worker {i} MD5: {d}")

        unique = set(digests)
        assert len(unique) == 1, (
            f"Expected all {N} concurrent identical requests to produce the "
            f"same MD5, but got {len(unique)} unique digests: {unique}"
        )


class TestFiveConcurrentRequests:
    """Five different parameter combinations processed concurrently
    must all succeed."""

    def test_five_concurrent_requests_all_succeed(self, synthetic_fingerprint):
        """5 different combos concurrently – all must return valid bytes."""
        combos = [
            {"design_id": "PDG040", "zone": 1, "mode": "emboss"},
            {"design_id": "PDG040", "zone": 2, "mode": "engrave"},
            {"design_id": "PDG040", "zone": 3, "mode": "emboss"},
            {"design_id": "P246",   "zone": 1, "mode": "emboss"},
            {"design_id": "P246",   "zone": 2, "mode": "engrave"},
        ]

        def _run(idx, combo):
            label = f"{combo['design_id']}-Z{combo['zone']}-{combo['mode']}"
            print(f"[{label}] Starting ...")
            result = generate_preview_stl(
                design_path=get_design_path(combo["design_id"]),
                fingerprint_file=synthetic_fingerprint,
                zones=[combo["zone"]],
                mode=combo["mode"],
                resolution=80,
            )
            stl_bytes = result[combo["zone"]]
            digest = _md5(stl_bytes)
            print(f"[{label}] Done – {len(stl_bytes)} bytes, MD5={digest}")
            return label, stl_bytes, digest

        results = {}
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {
                pool.submit(_run, i, c): i for i, c in enumerate(combos)
            }
            for future in as_completed(futures):
                label, data, digest = future.result()
                results[label] = (data, digest)

        print(f"\nAll {len(results)} concurrent requests completed.")
        for label, (data, digest) in results.items():
            print(f"  {label}: {len(data)} bytes, MD5={digest}")

        assert len(results) == 5, (
            f"Expected 5 successful results but got {len(results)}"
        )

        for label, (data, _) in results.items():
            assert isinstance(data, bytes) and len(data) > 0, (
                f"Request '{label}' returned invalid output"
            )
