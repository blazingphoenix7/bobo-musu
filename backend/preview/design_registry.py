"""Reads designs.json and auto-detects zone info from .3dm files.

Caches zone geometry on first access.
"""
import json
import sys
from pathlib import Path
from django.conf import settings

# Add the pipeline directory to sys.path for imports
_PIPELINE_DIR = str(settings.BASE_DIR.parent / "3dm files")
if _PIPELINE_DIR not in sys.path:
    sys.path.insert(0, _PIPELINE_DIR)

from fingerprint_displace import detect_zones, find_zone_face, find_zone_body
import rhino3dm

_cache = {}


def _load_config():
    """Load designs.json config."""
    config_path = settings.DESIGNS_CONFIG
    with open(config_path) as f:
        return json.load(f)


def _detect_zone_metadata(design_path, zone_num):
    """Detect metadata for a single zone from the .3dm file."""
    model = rhino3dm.File3dm.Read(str(design_path))
    _, _, face_brep = find_zone_face(model, zone_num)
    _, _, body_brep = find_zone_body(model, zone_num)

    face_bb = face_brep.GetBoundingBox()
    body_bb = body_brep.GetBoundingBox()
    thickness = abs(face_bb.Max.Z - body_bb.Min.Z)
    if thickness < 0.01:
        thickness = abs(body_bb.Max.Z - body_bb.Min.Z)

    face0 = face_brep.Faces[0]
    srf = face0.UnderlyingSurface()
    du, dv = srf.Domain(0), srf.Domain(1)
    u_mid = (du.T0 + du.T1) / 2
    v_mid = (dv.T0 + dv.T1) / 2
    nm = srf.NormalAt(u_mid, v_mid)
    if face0.OrientationIsReversed:
        nz = -nm.Z
    else:
        nz = nm.Z

    is_planar = abs(face_bb.Max.Z - face_bb.Min.Z) < 0.01
    faces_up = nz > 0

    return {
        "number": zone_num,
        "face_z": round(face_bb.Max.Z, 3),
        "thickness": round(thickness, 3),
        "is_planar": is_planar,
        "faces_up": faces_up,
        "mode_options": ["emboss", "engrave"],
    }


def _build_design_info(entry):
    """Build full design info dict, including auto-detected zones."""
    design_id = entry["id"]

    if design_id in _cache:
        return _cache[design_id]

    design_path = settings.DESIGNS_DIR / entry["filename"]
    if not design_path.exists():
        return None

    model = rhino3dm.File3dm.Read(str(design_path))
    zone_numbers = detect_zones(model)

    zones = []
    for z in zone_numbers:
        try:
            meta = _detect_zone_metadata(design_path, z)
            zones.append(meta)
        except SystemExit:
            continue

    info = {
        "id": design_id,
        "display_name": entry.get("display_name", design_id),
        "description": entry.get("description", ""),
        "filename": entry["filename"],
        "zones": zones,
        "has_gems": entry.get("has_gems", False),
    }
    _cache[design_id] = info
    return info


def get_designs():
    """Return all designs with zone metadata."""
    config = _load_config()
    results = []
    for entry in config.get("designs", []):
        info = _build_design_info(entry)
        if info is not None:
            results.append(info)
    return results


def get_design(design_id):
    """Return a single design with full zone metadata, or None."""
    config = _load_config()
    for entry in config.get("designs", []):
        if entry["id"] == design_id:
            return _build_design_info(entry)
    return None


def get_design_path(design_id):
    """Return the filesystem path to the .3dm file, or None."""
    config = _load_config()
    for entry in config.get("designs", []):
        if entry["id"] == design_id:
            path = settings.DESIGNS_DIR / entry["filename"]
            if path.exists():
                return path
    return None


def get_zone_count(design_id):
    """Return number of zones for a design."""
    design = get_design(design_id)
    if design is None:
        return 0
    return len(design["zones"])
