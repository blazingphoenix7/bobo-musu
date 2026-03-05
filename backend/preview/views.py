import base64
import struct

from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status

from .design_registry import get_designs, get_design, get_design_path
from .pipeline import generate_preview_stl, PipelineError

ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "BMP", "TIFF", "MPO"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


def _validate_image(file_obj):
    """Validate that the uploaded file is a supported image.

    Returns (is_valid, error_message).
    """
    if file_obj is None or file_obj.size == 0:
        return False, "No fingerprint image provided"

    if file_obj.size > MAX_UPLOAD_SIZE:
        return False, f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)}MB"

    from PIL import Image
    try:
        file_obj.seek(0)
        img = Image.open(file_obj)
        img.verify()
        file_obj.seek(0)
    except Exception:
        return False, "Invalid image format. Accepted: PNG, JPG, BMP, TIFF"

    if img.format not in ALLOWED_IMAGE_FORMATS:
        return False, f"Invalid image format '{img.format}'. Accepted: PNG, JPG, BMP, TIFF"

    return True, None


class DesignListView(APIView):
    """GET /api/designs/ — list all designs with zone info."""

    def get(self, request):
        designs = get_designs()
        data = []
        for d in designs:
            data.append({
                "id": d["id"],
                "display_name": d["display_name"],
                "description": d["description"],
                "zones": [z["number"] for z in d["zones"]],
                "has_gems": d.get("has_gems", False),
            })
        return Response({"designs": data})


class DesignDetailView(APIView):
    """GET /api/designs/{design_id}/ — single design detail."""

    def get(self, request, design_id):
        design = get_design(design_id)
        if design is None:
            return Response(
                {"error": "Design not found", "design_id": design_id},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        return Response({
            "id": design["id"],
            "display_name": design["display_name"],
            "description": design["description"],
            "zones": design["zones"],
        })


class DesignMeshView(APIView):
    """GET /api/designs/{design_id}/mesh/ — pre-exported base mesh OBJ."""

    def get(self, request, design_id):
        design = get_design(design_id)
        if design is None:
            return Response(
                {"error": "Design not found", "design_id": design_id},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        mesh_path = settings.MESHES_DIR / f"{design_id}_base.obj"
        if not mesh_path.exists():
            return Response(
                {"error": "Base mesh not available", "detail": "Pre-exported OBJ not found"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        obj_bytes = mesh_path.read_bytes()
        response = HttpResponse(obj_bytes, content_type="text/plain")
        response["Content-Disposition"] = f'attachment; filename="{design_id}_base.obj"'
        response["Cache-Control"] = "public, max-age=86400"
        return response


class PreviewView(APIView):
    """POST /api/preview/ — generate preview STL(s)."""

    def post(self, request):
        # --- Validate required fields ---
        fingerprint = request.FILES.get("fingerprint")
        design_id = request.data.get("design_id")
        zones_str = request.data.get("zones")
        mode = request.data.get("mode")

        if not fingerprint:
            return Response(
                {"error": "Missing required field: fingerprint"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if not design_id:
            return Response(
                {"error": "Missing required field: design_id"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if not zones_str:
            return Response(
                {"error": "Missing required field: zones"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if not mode:
            return Response(
                {"error": "Missing required field: mode"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # --- Validate image ---
        is_valid, error_msg = _validate_image(fingerprint)
        if not is_valid:
            return Response(
                {"error": error_msg},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # --- Validate design ---
        design = get_design(design_id)
        if design is None:
            return Response(
                {"error": "Design not found", "design_id": design_id},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        design_path = get_design_path(design_id)

        # --- Validate zones ---
        try:
            zones = [int(z.strip()) for z in zones_str.split(",")]
        except (ValueError, AttributeError):
            return Response(
                {"error": f"Invalid zones format. Expected comma-separated integers, got: {zones_str}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        valid_zones = [z["number"] for z in design["zones"]]
        invalid_zones = [z for z in zones if z not in valid_zones]
        if invalid_zones:
            return Response(
                {
                    "error": f"Invalid zone numbers. Design {design_id} has zones {valid_zones}",
                    "invalid_zones": invalid_zones,
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # --- Validate mode ---
        if mode not in ("emboss", "engrave"):
            return Response(
                {"error": "Mode must be 'emboss' or 'engrave'"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # --- Optional params ---
        defaults = settings.PIPELINE_DEFAULTS
        raw_depth = request.data.get("depth")
        if raw_depth is not None and raw_depth != "":
            try:
                depth = float(raw_depth)
            except (ValueError, TypeError):
                return Response(
                    {"error": "Depth must be a number between 0.01 and 2.0 mm"},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Auto-compute: 18% of EACH zone's thickness (per-zone depth)
            zone_meta = {z["number"]: z for z in design["zones"]}
            depth = {}
            for z in zones:
                if z in zone_meta and zone_meta[z]["thickness"] > 0:
                    d = round(zone_meta[z]["thickness"] * 0.18, 3)
                    depth[z] = max(0.02, min(d, 1.0))
                else:
                    depth[z] = defaults["depth"]

        try:
            resolution = int(request.data.get("resolution", defaults["resolution"]))
        except (ValueError, TypeError):
            return Response(
                {"error": "Resolution must be an integer between 50 and 500"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        unified = str(request.data.get("unified", "false")).lower() in ("true", "1")

        # Validate depth (scalar from user input, or per-zone dict from auto-compute)
        if isinstance(depth, (int, float)) and not (0.01 <= depth <= 2.0):
            return Response(
                {"error": "Depth must be between 0.01 and 2.0 mm"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        if not (50 <= resolution <= 500):
            return Response(
                {"error": "Resolution must be between 50 and 500"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        # --- Run pipeline ---
        try:
            stl_results = generate_preview_stl(
                design_path=design_path,
                fingerprint_file=fingerprint,
                zones=zones,
                mode=mode,
                depth=depth,
                resolution=resolution,
                unified=unified,
            )
        except PipelineError as e:
            detail = str(e)
            # Sanitize: don't leak filesystem paths
            for prefix in ("/Users/", "/home/", "/tmp/", "/var/"):
                if prefix in detail:
                    detail = "Pipeline processing failed"
                    break
            return Response(
                {"error": "Pipeline processing failed", "detail": detail},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception:
            return Response(
                {"error": "Pipeline processing failed", "detail": "Unexpected error"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Return result ---
        if len(zones) == 1:
            # Single zone: return binary STL directly
            zone_num = zones[0]
            stl_bytes = stl_results[zone_num]
            filename = f"{design_id}_zone{zone_num}_{mode}.stl"
            response = HttpResponse(stl_bytes, content_type="application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        else:
            # Multiple zones: return JSON with base64-encoded STLs
            zones_data = {}
            for zone_num, stl_bytes in stl_results.items():
                tri_count = struct.unpack("<I", stl_bytes[80:84])[0] if len(stl_bytes) >= 84 else 0
                zones_data[str(zone_num)] = {
                    "stl_base64": base64.b64encode(stl_bytes).decode("ascii"),
                    "filename": f"{design_id}_zone{zone_num}_{mode}.stl",
                    "triangle_count": tri_count,
                    "vertex_count": tri_count * 3,
                }
            return Response({
                "design_id": design_id,
                "mode": mode,
                "zones": zones_data,
            })
