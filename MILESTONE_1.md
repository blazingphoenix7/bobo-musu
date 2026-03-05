# Milestone 1: Fingerprint Preview — End-to-End

> **Goal:** A webpage where a user uploads a fingerprint image, picks a jewelry design, selects zones and mode (emboss/engrave), and sees a live 3D preview of the piece with their fingerprint applied.
>
> **No accounts. No Shopify. No payments. No database persistence beyond the session. Just the core magic working in a browser.**

---

## Environment

**All work must be done inside the `bobomusu` conda environment.**

```bash
# Activate before doing anything
conda activate bobomusu
```

All `pip install`, `python manage.py`, `pytest`, and any other commands must run inside this environment. If the environment doesn't have a dependency, install it there. Do not create a new virtual environment.

**RhinoMCP:** Rhino is running with the MCP server active. You have access to `mcp__rhino__*` tools for interacting with Rhino directly (creating/inspecting objects, capturing viewports, executing RhinoScript, etc.). Use these if you need to inspect or validate `.3dm` files visually during development or testing.

---

## What Already Exists

The displacement pipeline (`3dm files/fingerprint_displace.py`) is complete and tested. It takes:
- A `.3dm` jewelry design file with `FP_ZONE_N_FACE` / `FP_ZONE_N_BODY` layers
- A fingerprint image (PNG/JPG grayscale)
- Parameters: zone number(s), mode (emboss/engrave), depth, resolution

And produces:
- A modified `.3dm` file with displaced meshes on new `FP_ZONE_N_DISPLACED` layers
- STL files (binary) for each zone — suitable for 3D viewers and manufacturing

The pipeline supports:
- **Single zone** processing (`--zone 1`)
- **All zones** processing (`--all-zones`)
- **Unified mode** — one fingerprint mapped across all zones (`--all-zones --unified`)
- **Emboss** (raised ridges) and **engrave** (cut grooves)
- Configurable depth (default 0.3mm), resolution (default 250), feather width

Existing test designs:
- `PDG040.3dm` — 5 fingerprint zones
- `P246442LY.3dm` — 2 fingerprint zones

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Browser                           │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Upload   │  │ Design/Zone  │  │ 3D Viewer     │  │
│  │ Panel    │  │ Selector     │  │ (three.js)    │  │
│  └────┬─────┘  └──────┬───────┘  └───────▲───────┘  │
│       │               │                  │           │
└───────┼───────────────┼──────────────────┼───────────┘
        │               │                  │
        ▼               ▼                  │
┌─────────────────────────────────────────────────────┐
│                 Django Backend                        │
│                                                      │
│  POST /api/preview/                                  │
│    ← fingerprint image + design_id + zones + mode    │
│    → STL file bytes                                  │
│                                                      │
│  GET /api/designs/                                   │
│    → list of designs with zone info                  │
│                                                      │
│  GET /api/designs/{id}/                              │
│    → design detail with zone metadata                │
│                                                      │
│         ┌──────────────────────┐                     │
│         │ Pipeline Integration │                     │
│         │ (calls pipeline      │                     │
│         │  functions directly) │                     │
│         └──────────┬───────────┘                     │
│                    │                                 │
│         ┌──────────▼───────────┐                     │
│         │ fingerprint_displace │                     │
│         │ .py (existing)       │                     │
│         └──────────────────────┘                     │
│                                                      │
│  /designs/               ← .3dm design files         │
│  /tmp/preview_outputs/   ← ephemeral STL outputs     │
└─────────────────────────────────────────────────────┘
```

### Key Decisions

- **No database** for milestone 1. Design metadata is derived from the `.3dm` files themselves (auto-detect zones). A simple JSON config file maps design IDs to filenames and display names.
- **No user accounts.** No sessions. Stateless API.
- **Ephemeral processing.** Uploaded fingerprint → process → return STL → discard. No files stored permanently.
- **Pipeline called as a library**, not shelled out to CLI. Import the functions directly from `fingerprint_displace.py`.
- **STL returned directly** in the HTTP response. The browser's three.js viewer loads it client-side.
- **SQLite is fine** for Django internals (migrations, etc.) — we're not storing user data.

---

## Phase 1: Project Setup

### 1.1 Create Fresh Django Project

Delete or archive the entire existing `backend/` directory. Start fresh.

```
backend/
├── manage.py
├── pyproject.toml              ← dependencies (replaces Pipfile)
├── bobomusu/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── preview/                    ← the only Django app for milestone 1
│   ├── __init__.py
│   ├── urls.py
│   ├── views.py
│   ├── serializers.py
│   ├── pipeline.py             ← thin wrapper around fingerprint_displace.py
│   ├── design_registry.py      ← reads designs config, auto-detects zones
│   └── tests/                  ← ALL tests live here
│       ├── __init__.py
│       ├── conftest.py          ← pytest fixtures, shared config
│       ├── test_pipeline_integration.py
│       ├── test_api_designs.py
│       ├── test_api_preview.py
│       ├── test_upload_validation.py
│       ├── test_preview_output.py
│       ├── test_stl_integrity.py
│       ├── test_mesh_properties.py
│       ├── test_determinism.py
│       ├── test_error_handling.py
│       ├── test_stress.py
│       ├── test_end_to_end.py
│       ├── test_parametric.py
│       ├── test_concurrent.py
│       ├── test_cleanup.py
│       └── test_design_registry.py
├── designs/                    ← .3dm files (symlink or copy from "3dm files/designs/")
│   ├── PDG040.3dm
│   └── P246442LY.3dm
├── designs.json                ← design metadata config
├── static/                     ← frontend files
│   ├── index.html
│   ├── app.js
│   └── style.css
└── Dockerfile
```

### 1.2 Dependencies (`pyproject.toml`)

```toml
[project]
name = "bobomusu-backend"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "django>=5.1,<5.2",
    "djangorestframework>=3.15,<4",
    "django-cors-headers>=4.3,<5",
    "rhino3dm>=8.0.0",
    "numpy>=1.26",
    "scipy>=1.12",
    "Pillow>=10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-django>=4.8",
    "pytest-xdist>=3.5",        # parallel test execution
    "pytest-timeout>=2.2",       # timeout for stress tests
    "pytest-cov>=5.0",           # coverage
    "httpx>=0.27",               # async test client
    "ruff>=0.3",                 # linting
]
```

### 1.3 Settings (`bobomusu/settings.py`)

Minimal, modern Django 5.x settings. Only what's needed:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-replace-in-production")
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "preview",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bobomusu.urls"
WSGI_APPLICATION = "bobomusu.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# CORS — wide open for milestone 1 (no auth, no secrets)
CORS_ALLOW_ALL_ORIGINS = True

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

# ── App-specific ──
DESIGNS_DIR = BASE_DIR / "designs"
DESIGNS_CONFIG = BASE_DIR / "designs.json"

# Pipeline defaults
PIPELINE_DEFAULTS = {
    "depth": 0.3,
    "resolution": 200,       # lower than CLI default (250) for faster previews
    "feather": 10,
}

# Temp file cleanup
PREVIEW_TEMP_DIR = BASE_DIR / "tmp" / "preview_outputs"
```

### 1.4 Design Registry (`designs.json`)

```json
{
  "designs": [
    {
      "id": "PDG040",
      "filename": "PDG040.3dm",
      "display_name": "Pendant — 5 Zone",
      "description": "Pendant with 5 fingerprint zones"
    },
    {
      "id": "P246",
      "filename": "P246442LY.3dm",
      "display_name": "Pendant — 2 Zone",
      "description": "Pendant with 2 fingerprint zones"
    }
  ]
}
```

Zone info (count, bounding boxes, normals) is auto-detected from the `.3dm` files at startup by `design_registry.py`, not hardcoded.

---

## Phase 2: Pipeline Integration

### 2.1 `preview/pipeline.py` — Thin Wrapper

This module wraps `fingerprint_displace.py` functions for use by Django views. It does NOT shell out to the CLI — it imports and calls the functions directly.

```python
"""Thin wrapper around the fingerprint displacement pipeline.

Imports core functions from fingerprint_displace.py and exposes them
in a Django-friendly way (accepts file-like objects, returns bytes).
"""
```

**Functions to expose:**

```python
def generate_preview_stl(
    design_path: Path,
    fingerprint_file: UploadedFile,
    zones: list[int],
    mode: str = "emboss",
    depth: float = 0.3,
    resolution: int = 200,
    unified: bool = False,
) -> dict[int, bytes]:
    """Run the pipeline and return STL bytes per zone.

    Args:
        design_path: Path to the .3dm design file
        fingerprint_file: Uploaded fingerprint image (Django UploadedFile)
        zones: List of zone numbers to process
        mode: "emboss" or "engrave"
        depth: Max displacement in mm
        resolution: Grid resolution
        unified: If True, map one fingerprint across all zones

    Returns:
        Dict mapping zone number → STL file bytes
        Example: {1: b"...", 2: b"..."}
    """
```

**Implementation approach:**

1. Save uploaded fingerprint to a temp file
2. Call `preprocess_fingerprint()` from the pipeline
3. Read the design `.3dm` with `rhino3dm.File3dm.Read()`
4. For each zone, call `process_zone()` → get meshes
5. For each mesh, call `export_stl()` → write to temp file → read bytes
6. Clean up all temp files
7. Return the STL bytes dict

**Important:** Use `tempfile.TemporaryDirectory()` as a context manager so cleanup happens even if the pipeline crashes.

### 2.2 `preview/design_registry.py` — Design Metadata

```python
"""Reads designs.json and auto-detects zone info from .3dm files.

Caches zone geometry on first access (like combos.py's _geo_cache).
"""
```

**Functions:**

```python
def get_designs() -> list[dict]:
    """Return all designs with zone metadata.

    Returns:
        [
            {
                "id": "PDG040",
                "display_name": "Pendant — 5 Zone",
                "description": "...",
                "zones": [
                    {"number": 1, "mode_options": ["emboss", "engrave"]},
                    {"number": 2, "mode_options": ["emboss", "engrave"]},
                    ...
                ]
            },
            ...
        ]
    """

def get_design(design_id: str) -> dict | None:
    """Return a single design with full zone metadata, or None."""

def get_design_path(design_id: str) -> Path | None:
    """Return the filesystem path to the .3dm file, or None."""

def get_zone_count(design_id: str) -> int:
    """Return number of zones for a design."""
```

**Auto-detection:** Uses `detect_zones()` from `fingerprint_displace.py` to discover zone numbers from layer names. This means adding a new design is just: drop the `.3dm` file in `designs/`, add an entry to `designs.json`. No code changes.

---

## Phase 3: API Endpoints

### 3.1 URL Structure

```
GET  /api/designs/                     → list all designs with zone info
GET  /api/designs/{design_id}/         → single design detail
POST /api/preview/                     → generate preview STL(s)
GET  /                                 → serve the frontend (index.html)
```

### 3.2 `GET /api/designs/`

**Response:**
```json
{
  "designs": [
    {
      "id": "PDG040",
      "display_name": "Pendant — 5 Zone",
      "description": "Pendant with 5 fingerprint zones",
      "zones": [1, 2, 3, 4, 5]
    },
    {
      "id": "P246",
      "display_name": "Pendant — 2 Zone",
      "description": "Pendant with 2 fingerprint zones",
      "zones": [1, 2]
    }
  ]
}
```

### 3.3 `GET /api/designs/{design_id}/`

**Response:**
```json
{
  "id": "PDG040",
  "display_name": "Pendant — 5 Zone",
  "description": "Pendant with 5 fingerprint zones",
  "zones": [
    {
      "number": 1,
      "face_z": 5.123,
      "thickness": 2.5,
      "is_planar": true,
      "faces_up": true
    },
    ...
  ]
}
```

**Error (404):**
```json
{"error": "Design not found", "design_id": "INVALID"}
```

### 3.4 `POST /api/preview/`

**Request:** `multipart/form-data`

| Field         | Type   | Required | Description                                     |
|---------------|--------|----------|-------------------------------------------------|
| `fingerprint` | file   | yes      | Fingerprint image (PNG, JPG, BMP, TIFF)         |
| `design_id`   | string | yes      | Design identifier (e.g., `PDG040`)              |
| `zones`       | string | yes      | Comma-separated zone numbers (e.g., `1,2,3`)   |
| `mode`        | string | yes      | `emboss` or `engrave`                           |
| `depth`       | float  | no       | Max displacement mm (default: 0.3)              |
| `resolution`  | int    | no       | Grid resolution (default: 200)                  |
| `unified`     | bool   | no       | Unified fingerprint mapping (default: false)    |

**Response (single zone):** Binary STL file

```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="PDG040_zone1_emboss.stl"
```

**Response (multiple zones):** JSON with base64-encoded STLs

```json
{
  "design_id": "PDG040",
  "mode": "emboss",
  "zones": {
    "1": {
      "stl_base64": "<base64 encoded STL bytes>",
      "filename": "PDG040_zone1_emboss.stl",
      "triangle_count": 12450,
      "vertex_count": 6300
    },
    "2": {
      "stl_base64": "<base64 encoded STL bytes>",
      "filename": "PDG040_zone2_emboss.stl",
      "triangle_count": 11200,
      "vertex_count": 5700
    }
  }
}
```

**Validation errors (400):**
```json
{"error": "Invalid image format. Accepted: PNG, JPG, BMP, TIFF"}
{"error": "Design not found", "design_id": "BADID"}
{"error": "Invalid zone numbers. Design PDG040 has zones [1, 2, 3, 4, 5]", "invalid_zones": [7]}
{"error": "Mode must be 'emboss' or 'engrave'"}
{"error": "Depth must be between 0.01 and 2.0 mm"}
{"error": "Resolution must be between 50 and 500"}
```

**Pipeline errors (500):**
```json
{"error": "Pipeline processing failed", "detail": "No grid points inside the trim boundary"}
```

---

## Phase 4: Frontend

### 4.1 Overview

A single `index.html` served by Django's static files. No build step, no npm, no framework. Plain HTML + vanilla JS + three.js via CDN.

### 4.2 Layout

```
┌─────────────────────────────────────────────────────┐
│  Bobo & Musu — Fingerprint Preview                  │
├───────────────────────┬─────────────────────────────┤
│                       │                             │
│  [Upload Fingerprint] │                             │
│  ┌─────────────────┐  │     ┌───────────────────┐   │
│  │  Drop image     │  │     │                   │   │
│  │  or click       │  │     │   3D Viewer       │   │
│  └─────────────────┘  │     │   (three.js)      │   │
│                       │     │                   │   │
│  Design:              │     │   Orbit / Zoom    │   │
│  ┌─────────────────┐  │     │   Pan controls    │   │
│  │ PDG040 (5 zone) ▼│ │     │                   │   │
│  └─────────────────┘  │     └───────────────────┘   │
│                       │                             │
│  Zones:               │                             │
│  ☑ Zone 1  ☑ Zone 2  │                             │
│  ☑ Zone 3  ☐ Zone 4  │                             │
│  ☐ Zone 5            │                             │
│                       │                             │
│  Mode: ◉ Emboss       │                             │
│        ○ Engrave      │                             │
│                       │                             │
│  ☐ Unified mapping   │                             │
│                       │                             │
│  Depth: [0.3] mm     │                             │
│                       │                             │
│  [ Generate Preview ] │                             │
│                       │                             │
│  Status: Processing..│                             │
│                       │                             │
├───────────────────────┴─────────────────────────────┤
│  Pipeline: 3.2s │ Triangles: 24,600 │ Zones: 2     │
└─────────────────────────────────────────────────────┘
```

### 4.3 Frontend Behavior

1. **On page load:** Fetch `GET /api/designs/` → populate design dropdown
2. **On design select:** Fetch `GET /api/designs/{id}/` → show zone checkboxes based on detected zones
3. **Upload fingerprint:** Drag-and-drop or file picker. Show thumbnail preview. Client-side validation: must be an image, reasonable file size (<10MB).
4. **Generate Preview:** POST to `/api/preview/` with form data. Show loading spinner. On success, load the STL(s) into the three.js viewer.
5. **3D Viewer:** three.js `STLLoader` renders the mesh. Orbit controls for rotation, zoom, pan. If multiple zones, load all STLs into the same scene.
6. **Error display:** Show API error messages inline below the Generate button.

### 4.4 three.js Setup

Use CDN imports (no build step):

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }
}
</script>
```

Load STL with `STLLoader`, render with `MeshStandardMaterial` (metallic look for jewelry), add `OrbitControls`, ambient + directional lights.

---

## Phase 5: Testing

> **Philosophy:** Replicate the exhaustive, multi-tier, parametric testing approach from `3dm files/output/tests/`. Every layer of the system gets its own tier of tests. Tests are parameterized across all design/zone/mode combinations. Assertions are cumulative (don't fail-fast). Output is informative.

### 5.0 Shared Test Configuration (`conftest.py`)

The equivalent of `combos.py` for the web layer.

```python
"""Shared fixtures and configuration for all tests.

Mirrors the philosophy of 3dm files/output/tests/combos.py:
- Parametric test matrix across designs, zones, modes
- Cached geometry lookups
- Informative output on every assertion
"""
import pytest
import json
from pathlib import Path
from django.conf import settings

# ── Test Matrix ──────────────────────────────────────────────────

DESIGNS = ["PDG040", "P246"]
MODES = ["emboss", "engrave"]

# Full parametric matrix: (design_id, zone, mode)
# Auto-detected from actual .3dm files at test collection time
def _build_combo_matrix():
    """Build test combos from actual design files (like combos.ALL_COMBOS)."""
    from preview.design_registry import get_designs
    combos = []
    for design in get_designs():
        for zone in design["zones"]:
            for mode in MODES:
                combos.append((design["id"], zone, mode))
    return combos

ALL_COMBOS = _build_combo_matrix()

# Pytest parametrize helpers
def combo_id(combo):
    """Human-readable test ID: 'PDG040-Z1-emboss'"""
    return f"{combo[0]}-Z{combo[1]}-{combo[2]}"

# ── Fixtures ─────────────────────────────────────────────────────

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
```

### 5.1 Design Registry Tests (`test_design_registry.py`)

**What:** The design registry correctly reads `designs.json`, auto-detects zones from `.3dm` files, and caches results.

```
TESTS:
├── test_all_designs_load
│   Assert designs.json parses without error
│   Assert at least 1 design returned
│   Assert every design has: id, display_name, filename, zones
│
├── test_zone_autodetection_matches_known_counts
│   PDG040 → exactly 5 zones [1, 2, 3, 4, 5]
│   P246   → exactly 2 zones [1, 2]
│
├── test_zone_numbers_are_sorted
│   For each design: zones list is sorted ascending
│
├── test_design_files_exist_on_disk
│   For each design in config: .3dm file exists at expected path
│
├── test_get_design_returns_none_for_invalid_id
│   get_design("NONEXISTENT") returns None
│
├── test_get_design_path_returns_valid_path
│   For each design: path exists and is a file
│
├── test_zone_geometry_cache_consistency
│   Call get_design() twice → same object (cached)
│   Zone metadata identical between calls
│
├── test_designs_json_schema_valid
│   Every entry has required fields
│   No duplicate IDs
│   No duplicate filenames
│
└── test_registry_survives_missing_3dm_file
    If a designs.json entry points to a nonexistent file:
    Registry loads without crashing
    That design is excluded or marked as unavailable
```

### 5.2 Pipeline Integration Tests (`test_pipeline_integration.py`)

**What:** The `pipeline.py` wrapper correctly calls the displacement pipeline and returns valid results.

```
TESTS (parameterized across ALL_COMBOS):
├── test_generate_preview_stl_returns_bytes
│   For each (design, zone, mode):
│     Call generate_preview_stl()
│     Assert return type is dict[int, bytes]
│     Assert zone key present
│     Assert bytes length > 100
│
├── test_stl_output_is_valid_binary_stl
│   For each combo:
│     Parse returned bytes as binary STL
│     Assert 80-byte header
│     Assert triangle count > 0
│     Assert file size == 80 + 4 + (50 * triangle_count)
│
├── test_emboss_and_engrave_produce_different_output
│   For each (design, zone):
│     Generate emboss STL
│     Generate engrave STL
│     Assert bytes are different (not identical)
│
├── test_multiple_zones_returns_all_requested
│   For PDG040: request zones [1, 2, 3]
│   Assert result dict has keys {1, 2, 3}
│   Each value is non-empty bytes
│
├── test_unified_mode_produces_output
│   For each design with 2+ zones:
│     Request all zones with unified=True
│     Assert result has all zone keys
│
├── test_depth_parameter_affects_output
│   Same design/zone/mode at depth=0.1 vs depth=0.5
│   Assert outputs differ
│
├── test_resolution_parameter_affects_vertex_count
│   Same combo at resolution=100 vs resolution=300
│   Parse both STLs, count triangles
│   Assert higher resolution → more triangles
│
├── test_temp_files_cleaned_up_after_processing
│   Note files in temp dir before call
│   Call generate_preview_stl()
│   Note files in temp dir after call
│   Assert no new files remain
│
├── test_invalid_fingerprint_raises_error
│   Pass a non-image file (text file, empty file, binary garbage)
│   Assert appropriate exception raised
│
└── test_invalid_zone_raises_error
    Request zone 99 for PDG040 (only has 1-5)
    Assert appropriate exception raised
```

### 5.3 API Designs Endpoint Tests (`test_api_designs.py`)

**What:** The designs list and detail endpoints return correct data.

```
TESTS:
├── test_list_designs_returns_200
│   GET /api/designs/ → 200
│
├── test_list_designs_response_structure
│   Response has "designs" key
│   Each design has: id, display_name, description, zones
│   zones is a non-empty list of integers
│
├── test_list_designs_contains_all_known_designs
│   Response includes PDG040 and P246
│
├── test_design_detail_returns_200_for_valid_id
│   GET /api/designs/PDG040/ → 200
│   GET /api/designs/P246/ → 200
│
├── test_design_detail_response_structure
│   Has: id, display_name, description, zones
│   zones is list of objects with: number, is_planar, faces_up
│
├── test_design_detail_returns_404_for_invalid_id
│   GET /api/designs/NONEXISTENT/ → 404
│   Response has "error" key
│
├── test_design_detail_zone_count_matches_list
│   List endpoint zone count == detail endpoint zone count
│   For every design
│
├── test_designs_endpoint_is_idempotent
│   Call GET /api/designs/ twice
│   Assert identical responses
│
├── test_designs_endpoint_allows_only_get
│   POST /api/designs/ → 405
│   PUT /api/designs/ → 405
│   DELETE /api/designs/ → 405
│
└── test_content_type_is_json
    All responses have Content-Type: application/json
```

### 5.4 API Preview Endpoint Tests (`test_api_preview.py`)

**What:** The preview endpoint handles valid requests, returns correct data, and rejects bad requests.

```
TESTS (parameterized across ALL_COMBOS where applicable):
├── test_valid_single_zone_request_returns_200
│   POST with valid fingerprint + design + zone + mode → 200
│
├── test_valid_multi_zone_request_returns_200
│   POST with zones=1,2,3 for PDG040 → 200
│
├── test_single_zone_returns_binary_stl
│   Content-Type is application/octet-stream
│   Body is non-empty bytes
│   Content-Disposition has .stl filename
│
├── test_multi_zone_returns_json_with_base64_stls
│   Content-Type is application/json
│   Response has per-zone stl_base64 fields
│   Each base64 decodes to valid STL bytes
│
├── test_missing_fingerprint_returns_400
│   POST without fingerprint file → 400
│   Error message mentions "fingerprint"
│
├── test_missing_design_id_returns_400
│   POST without design_id → 400
│
├── test_missing_zones_returns_400
│   POST without zones → 400
│
├── test_missing_mode_returns_400
│   POST without mode → 400
│
├── test_invalid_design_id_returns_400
│   POST with design_id="FAKE" → 400
│   Error message mentions the invalid ID
│
├── test_invalid_zone_numbers_returns_400
│   POST zones=99 for PDG040 → 400
│   Error message lists valid zones
│
├── test_invalid_mode_returns_400
│   POST mode="carve" → 400
│
├── test_invalid_image_format_returns_400
│   POST a .txt file as fingerprint → 400
│   POST a .pdf as fingerprint → 400
│   POST empty file as fingerprint → 400
│
├── test_depth_out_of_range_returns_400
│   depth=0.0 → 400
│   depth=-1.0 → 400
│   depth=10.0 → 400
│
├── test_resolution_out_of_range_returns_400
│   resolution=5 → 400
│   resolution=2000 → 400
│
├── test_optional_params_use_defaults
│   POST without depth/resolution → 200
│   Pipeline uses configured defaults
│
├── test_unified_flag_accepted
│   POST with unified=true, zones=1,2 → 200
│
├── test_preview_only_accepts_post
│   GET /api/preview/ → 405
│   PUT /api/preview/ → 405
│
└── test_large_fingerprint_image_accepted
    POST a 4000x4000 PNG → 200 (pipeline downsamples)
```

### 5.5 Upload Validation Tests (`test_upload_validation.py`)

**What:** Image upload validation is robust and secure.

```
TESTS:
├── test_png_accepted
├── test_jpg_accepted
├── test_jpeg_accepted
├── test_bmp_accepted
├── test_tiff_accepted
├── test_grayscale_image_accepted
├── test_rgb_image_accepted_and_converted
├── test_rgba_image_accepted_and_converted
│
├── test_gif_rejected
├── test_svg_rejected
├── test_webp_decision
│   (Accept or reject — document the decision)
│
├── test_zero_byte_file_rejected
├── test_non_image_with_png_extension_rejected
│   Rename a .txt to .png → still rejected (check magic bytes)
│
├── test_truncated_image_rejected
│   Valid PNG header but truncated body
│
├── test_image_size_limit_enforced
│   >10MB file → 400 with clear error
│
├── test_very_small_image_accepted
│   1x1 pixel → accepted (pipeline handles it)
│
├── test_very_large_dimensions_accepted
│   8000x8000 → accepted (pipeline downsamples)
│
└── test_image_with_exif_metadata_accepted
    JPEG with EXIF rotation → accepted, handled correctly
```

### 5.6 STL Output Integrity Tests (`test_stl_integrity.py`)

**What:** Every STL returned by the API is a valid binary STL. Mirrors the 3dm test suite's file integrity checks.

```
TESTS (parameterized across ALL_COMBOS):
├── test_stl_has_80_byte_header
│   First 80 bytes are header (any content)
│
├── test_stl_triangle_count_field_matches_actual
│   Bytes 80-83 (uint32 LE) == number of 50-byte triangle records
│
├── test_stl_file_size_matches_formula
│   Total size == 80 + 4 + (50 * triangle_count)
│   No trailing bytes
│
├── test_stl_all_triangles_readable
│   Can read all triangle_count records of 50 bytes each
│   Each record: 12 floats (normal + 3 vertices) + 2 byte attribute
│
├── test_stl_no_nan_values
│   Parse all vertex/normal floats
│   Assert none are NaN
│
├── test_stl_no_inf_values
│   Parse all vertex/normal floats
│   Assert none are +/-Inf
│
├── test_stl_vertices_in_reasonable_range
│   All vertex coordinates in [-1000, 1000] mm
│   (Jewelry is typically < 50mm in any dimension)
│
├── test_stl_normals_are_unit_length
│   For each triangle: |normal| ≈ 1.0 (tolerance 0.01)
│   OR |normal| ≈ 0 (degenerate — pipeline filters these)
│
├── test_stl_no_degenerate_triangles
│   For each triangle: area > 1e-10
│   (Pipeline's export_stl already filters these, verify it works through the API)
│
└── test_stl_triangle_count_nonzero
    Every response has at least 1 triangle
```

### 5.7 Mesh Property Tests (`test_mesh_properties.py`)

**What:** The mesh geometry returned through the API has correct properties. Mirrors the 3dm suite's mesh topology, face normal, and bounding box tests.

```
TESTS (parameterized across ALL_COMBOS):
├── test_vertex_count_scales_with_resolution
│   res=100 → V₁ vertices
│   res=200 → V₂ vertices
│   Assert V₂ > V₁ (more resolution = more vertices)
│
├── test_triangle_count_positive
│   For each combo: triangle_count > 0
│
├── test_bounding_box_within_design_bounds
│   Mesh BB fits within the design's overall BB
│   (STL vertices don't exceed design extents + depth tolerance)
│
├── test_face_normals_consistent_with_mode
│   Emboss: majority of face normals point outward (same as surface normal)
│   Engrave: majority of face normals point inward
│
├── test_mesh_has_no_isolated_vertices
│   Every vertex is referenced by at least one triangle
│
├── test_edge_lengths_in_reasonable_range
│   No edge shorter than 1e-6 mm (degenerate)
│   No edge longer than 20 mm (reasonable for jewelry zone)
│
├── test_triangle_aspect_ratios_reasonable
│   99th percentile aspect ratio < 100
│   (Some slivers at boundaries are OK, but not dominant)
│
├── test_mesh_is_connected
│   All triangles form a single connected component
│   (No floating islands)
│
├── test_emboss_vertices_above_or_at_surface
│   For emboss mode: displaced Z >= original face Z (within tolerance)
│
├── test_engrave_vertices_below_or_at_surface
│   For engrave mode: displaced Z <= original face Z (within tolerance)
│
├── test_displacement_magnitude_within_depth
│   For each vertex: |displacement| <= depth * 1.01
│   (1% tolerance for floating point)
│
└── test_feather_creates_smooth_boundary
    Vertices near the zone boundary have smaller displacement
    than vertices near the center (feathering works)
```

### 5.8 Determinism Tests (`test_determinism.py`)

**What:** Same inputs → identical outputs. Critical for manufacturing.

```
TESTS (parameterized across ALL_COMBOS):
├── test_same_request_produces_identical_stl_bytes
│   Send identical POST twice
│   Assert response bytes are byte-for-byte identical
│   (MD5 hash comparison, like the 3dm determinism test)
│
├── test_determinism_across_ten_runs
│   Same request 10 times
│   All 10 MD5 hashes identical
│
├── test_different_fingerprint_produces_different_output
│   Same design/zone/mode, two different fingerprint images
│   Assert outputs differ
│
├── test_different_zone_produces_different_output
│   Same design/fingerprint/mode, different zones
│   Assert outputs differ
│
└── test_different_mode_produces_different_output
    Same design/zone/fingerprint, emboss vs engrave
    Assert outputs differ
```

### 5.9 Error Handling Tests (`test_error_handling.py`)

**What:** The API handles all failure modes gracefully without crashing, leaking temp files, or returning 500s for user errors.

```
TESTS:
├── test_corrupted_3dm_file_returns_500_with_message
│   (Simulate by temporarily replacing a .3dm with garbage)
│
├── test_pipeline_timeout_handled
│   (If resolution is absurdly high and times out)
│
├── test_concurrent_requests_dont_interfere
│   Send 5 requests simultaneously
│   All return valid, independent results
│
├── test_temp_dir_creation_failure_handled
│   (If PREVIEW_TEMP_DIR is not writable)
│
├── test_api_errors_never_leak_filesystem_paths
│   For every 4xx/5xx response:
│   Assert response body does not contain absolute file paths
│   Assert no /Users/, /home/, /tmp/ in error messages
│
├── test_api_errors_are_json
│   Every error response is valid JSON with "error" key
│
├── test_oversized_upload_rejected_before_processing
│   Send a 100MB file
│   Assert 400 returned quickly (not after trying to process)
│
└── test_malformed_multipart_returns_400
    Send invalid multipart form data → 400, not 500
```

### 5.10 Stress Tests (`test_stress.py`)

**What:** The system handles extreme inputs without crashing. Mirrors the 3dm suite's `test_stress.py`.

```
TESTS:
├── test_max_resolution_completes
│   resolution=500, single zone
│   Assert completes in < 120 seconds
│   Assert valid STL output
│
├── test_all_zones_max_design_completes
│   PDG040 all 5 zones at default resolution
│   Assert completes in < 60 seconds
│   Assert all 5 STLs valid
│
├── test_1px_fingerprint_doesnt_crash
│   Upload a 1x1 pixel image
│   Assert either valid output or clean error (no crash)
│
├── test_pure_white_fingerprint
│   Upload all-white image → should produce flat surface (no displacement)
│
├── test_pure_black_fingerprint
│   Upload all-black image → should produce max displacement everywhere
│
├── test_gradient_fingerprint
│   Upload linear gradient → smooth displacement transition
│
├── test_high_contrast_fingerprint
│   Upload checkerboard pattern → valid mesh, no degenerate triangles
│
├── test_very_small_depth
│   depth=0.01 mm → valid output, displacement barely visible
│
├── test_very_large_depth
│   depth=2.0 mm → clamped by pipeline if exceeds zone thickness
│
└── test_rapid_sequential_requests
    Send 20 requests in rapid succession (not concurrent, sequential)
    All return valid results
    No temp file accumulation
```

### 5.11 End-to-End Tests (`test_end_to_end.py`)

**What:** Full user flow through the API. The closest thing to testing the actual product experience.

```
TESTS:
├── test_full_flow_single_zone
│   1. GET /api/designs/ → pick first design
│   2. GET /api/designs/{id}/ → note zone numbers
│   3. POST /api/preview/ with zone 1 + emboss
│   4. Assert valid STL in response
│   5. Parse STL, verify triangle count > 0
│
├── test_full_flow_multi_zone
│   Same as above but with multiple zones
│   Verify each zone has independent STL data
│
├── test_full_flow_all_modes
│   For a single design/zone:
│   Generate emboss preview
│   Generate engrave preview
│   Verify both are valid and different
│
├── test_full_flow_unified
│   For PDG040 (5 zones):
│   Request all zones unified
│   Verify all 5 STLs returned
│
├── test_full_flow_with_real_fingerprint_image
│   Use the actual test fingerprint from 3dm files/fingerprints/
│   (Not synthetic — a real preprocessed fingerprint)
│   Verify the entire flow works with real data
│
├── test_preview_then_different_design
│   Preview PDG040 zone 1
│   Then preview P246 zone 1
│   Both return valid, different results
│
├── test_preview_then_different_fingerprint
│   Preview with fingerprint A
│   Then preview same design/zone/mode with fingerprint B
│   Both valid, different results
│
└── test_stl_loadable_by_three_js_stl_loader
    Parse the STL bytes using the same algorithm three.js uses:
    - Read 80-byte header
    - Read uint32 triangle count
    - Read N * 50-byte triangle records
    - Build vertex array
    Assert vertex array is non-empty and has valid floats
    (This catches issues that would break the frontend viewer)
```

### 5.12 Concurrent Request Tests (`test_concurrent.py`)

**What:** Multiple simultaneous requests don't corrupt each other.

```
TESTS:
├── test_two_different_designs_concurrent
│   POST PDG040-Z1-emboss and P246-Z1-emboss simultaneously
│   Assert both return valid, different results
│   Assert no file path collisions in temp dir
│
├── test_same_request_concurrent
│   POST identical request 3 times simultaneously
│   Assert all 3 responses are byte-identical (determinism under concurrency)
│
├── test_five_concurrent_requests_all_succeed
│   5 different combos in parallel
│   All return 200
│   All return valid STL
│
└── test_concurrent_requests_cleanup_temp_files
    After all concurrent requests complete:
    Temp directory is empty (all cleaned up)
```

### 5.13 Temp File Cleanup Tests (`test_cleanup.py`)

**What:** No temp files leak, even on errors.

```
TESTS:
├── test_successful_request_leaves_no_temp_files
│   Count files in temp dir before
│   POST valid request
│   Count files in temp dir after
│   Assert count unchanged
│
├── test_failed_request_leaves_no_temp_files
│   Count before
│   POST invalid request (bad image)
│   Count after
│   Assert count unchanged
│
├── test_pipeline_crash_leaves_no_temp_files
│   Force a pipeline error (e.g., corrupted design file)
│   Assert temp dir is clean
│
└── test_temp_dir_is_created_if_missing
    Delete temp dir
    POST valid request
    Assert succeeds (temp dir auto-created)
```

### 5.14 Parametric Cross-Combo Tests (`test_parametric.py`)

**What:** Properties that should hold across ALL design/zone/mode combinations. The web-layer equivalent of the 3dm suite's `test_allzones_*` battery.

```
TESTS (parameterized across EVERY combo in ALL_COMBOS):
├── test_every_combo_returns_200
│   Every (design, zone, mode) → 200
│
├── test_every_combo_returns_nonzero_triangles
│   Parse STL, triangle_count > 0
│
├── test_every_combo_stl_is_valid_binary
│   80-byte header + count + records, no trailing bytes
│
├── test_every_combo_no_nan_vertices
│   No NaN in any vertex coordinate
│
├── test_every_combo_vertices_in_bounds
│   All vertices within [-500, 500] mm
│
├── test_every_combo_has_reasonable_triangle_count
│   At default resolution: 1,000 < triangles < 500,000
│
├── test_every_combo_stl_file_size_reasonable
│   100 bytes < size < 50 MB
│
├── test_every_combo_different_from_every_other
│   No two different combos produce identical STL bytes
│   (Different zone/mode must produce different geometry)
│
├── test_emboss_engrave_pairs_have_same_triangle_count
│   For each (design, zone):
│   emboss triangle_count == engrave triangle_count
│   (Same grid, same topology, only displacement direction differs)
│
└── test_all_designs_all_zones_processable
    For each design: every detected zone processes successfully
    No "dead" zones that crash the pipeline
```

### 5.15 Frontend Tests (Manual Checklist + Automated Smoke)

For milestone 1, frontend testing is lighter. Automated where possible, manual checklist otherwise.

**Automated (`test_frontend_smoke.py`):**
```
├── test_index_page_returns_200
│   GET / → 200
│
├── test_index_page_contains_required_elements
│   Response HTML contains:
│   - file upload input
│   - design selector
│   - mode radio buttons
│   - generate button
│   - 3D viewer canvas/container
│
├── test_static_files_served
│   GET /static/app.js → 200
│   GET /static/style.css → 200
│
└── test_three_js_cdn_url_in_page
    Response HTML contains three.js import
```

**Manual Checklist:**
```
□ Page loads without console errors
□ Design dropdown populates on load
□ Zone checkboxes update when design changes
□ Fingerprint upload shows thumbnail
□ Drag-and-drop upload works
□ Generate button triggers API call
□ Loading spinner shows during processing
□ 3D viewer renders STL after processing
□ Orbit controls work (click + drag to rotate)
□ Zoom works (scroll wheel)
□ Multiple zones render in same viewer
□ Error messages display for bad uploads
□ Switching designs and re-generating works
□ Switching modes and re-generating works
```

---

## Phase 6: Running Tests

### Test Commands

```bash
# Run all tests
pytest backend/preview/tests/ -v

# Run a specific test tier
pytest backend/preview/tests/test_stl_integrity.py -v

# Run only PDG040 combos (via marker or -k filter)
pytest -k "PDG040" -v

# Run only emboss tests
pytest -k "emboss" -v

# Run with coverage
pytest --cov=preview --cov-report=term-missing -v

# Run stress tests with timeout
pytest backend/preview/tests/test_stress.py -v --timeout=300

# Run tests in parallel (faster)
pytest -n auto -v

# Run the full parametric battery (slowest, most thorough)
pytest backend/preview/tests/test_parametric.py -v --timeout=600
```

### Expected Test Counts

| Test File                      | Approx. Test Count | Notes                             |
|-------------------------------|--------------------|-----------------------------------|
| `test_design_registry.py`     | 10                 | Fixed count                       |
| `test_pipeline_integration.py`| 14 × 3 + 8 ≈ 50   | Parametric + standalone           |
| `test_api_designs.py`         | 12                 | Fixed count                       |
| `test_api_preview.py`         | 14 × 2 + 16 ≈ 44  | Parametric + validation           |
| `test_upload_validation.py`   | 18                 | Fixed count                       |
| `test_stl_integrity.py`       | 14 × 10 = 140     | Full parametric                   |
| `test_mesh_properties.py`     | 14 × 12 = 168     | Full parametric                   |
| `test_determinism.py`         | 14 × 3 + 2 = 44   | Parametric + extras               |
| `test_error_handling.py`      | 8                  | Fixed count                       |
| `test_stress.py`              | 10                 | Fixed count                       |
| `test_end_to_end.py`          | 8                  | Fixed count                       |
| `test_concurrent.py`          | 4                  | Fixed count                       |
| `test_cleanup.py`             | 4                  | Fixed count                       |
| `test_parametric.py`          | 14 × 10 = 140     | Full parametric                   |
| `test_frontend_smoke.py`      | 4                  | Fixed count                       |
| **TOTAL**                     | **~660+**          |                                   |

---

## Phase 7: Definition of Done

Milestone 1 is complete when:

1. `GET /api/designs/` returns all designs with correct zone counts
2. `GET /api/designs/{id}/` returns zone metadata auto-detected from `.3dm` files
3. `POST /api/preview/` accepts a fingerprint image + design + zones + mode and returns valid STL bytes
4. The STL bytes are valid binary STL files that pass all integrity checks
5. The webpage loads, shows a design picker, accepts fingerprint upload, and renders a 3D preview
6. The three.js viewer displays the displaced mesh with orbit/zoom controls
7. All 660+ tests pass
8. No temp files leak under any circumstance
9. Error messages are clear and never expose server internals
10. A non-technical person can use it: upload fingerprint → see their fingerprint on the jewelry

---

## Order of Implementation

Build and test in this order. Each step should be fully tested before moving to the next.

```
Step 1: Project scaffolding
         └─ Django project, settings, dependencies, pytest config
         └─ TEST: Django boots, pytest discovers tests

Step 2: Design registry
         └─ designs.json, design_registry.py, zone auto-detection
         └─ TEST: test_design_registry.py passes (all 10)

Step 3: Pipeline integration
         └─ pipeline.py wrapper, import fingerprint_displace functions
         └─ TEST: test_pipeline_integration.py passes (all ~50)

Step 4: API endpoints — designs
         └─ GET /api/designs/, GET /api/designs/{id}/
         └─ TEST: test_api_designs.py passes (all 12)

Step 5: API endpoint — preview
         └─ POST /api/preview/
         └─ TEST: test_api_preview.py passes (all ~44)

Step 6: Upload validation
         └─ Image validation, format checks, size limits
         └─ TEST: test_upload_validation.py passes (all 18)

Step 7: STL + mesh validation battery
         └─ (No new code — these test existing output quality)
         └─ TEST: test_stl_integrity.py passes (all 140)
         └─ TEST: test_mesh_properties.py passes (all 168)

Step 8: Determinism + error handling + stress
         └─ Temp file cleanup, concurrency safety
         └─ TEST: test_determinism.py, test_error_handling.py,
                  test_stress.py, test_concurrent.py, test_cleanup.py

Step 9: Parametric cross-combo battery
         └─ (No new code — final comprehensive validation)
         └─ TEST: test_parametric.py passes (all 140)

Step 10: Frontend
          └─ index.html, app.js, style.css, three.js viewer
          └─ TEST: test_frontend_smoke.py + manual checklist

Step 11: End-to-end
          └─ Full flow testing
          └─ TEST: test_end_to_end.py passes (all 8)
```

---

## Notes for the Implementer

- **Do NOT touch `fingerprint_displace.py`**. It works. Import its functions; don't modify them. If something needs adapting for web use, write the adapter in `pipeline.py`.
- **Designs directory:** Symlink or copy `.3dm` files from `3dm files/designs/` into `backend/designs/`. The pipeline test data stays where it is.
- **Python path:** `pipeline.py` needs to import from `fingerprint_displace.py`. Handle this with `sys.path` manipulation in `pipeline.py`, or better, copy/symlink the script into the backend and treat it as a library module.
- **three.js version:** Pin the CDN version (e.g., 0.170.0). Don't use "latest" — it can break the STLLoader API between versions.
- **File size:** STL files for a single zone at resolution 200 are typically 1-5 MB. The frontend should handle this without issues. For multi-zone responses (JSON + base64), responses can be 10-20 MB.
- **Resolution default:** Use 200 for previews (fast), not 250 (the CLI default). Users can bump it up if they want sharper previews. Manufacturing runs can use 400-500.
- **Test philosophy:** Tests should be VERBOSE. Print what they're checking, what values they found, and whether it passed. Don't just assert silently. When a test fails, the output alone should tell you what went wrong without needing a debugger.
