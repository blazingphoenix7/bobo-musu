# Casting-Ready STL Pipeline — Design Spec

## Goal

Produce a single closed watertight STL file from any designer's .3dm + a customer's fingerprint image. The STL must be ready to drag into a wax printer for lost-wax casting — no manual cleanup by the designer or caster.

## Current State

The pipeline currently outputs:
- A `.3dm` file with the original design + separate displacement mesh objects on `FP_ZONE_N_DISPLACED` layers
- Per-zone STL files (watertight shells, but NOT merged into the body)

The displacement meshes float on top of the body as separate objects. A caster cannot print this directly.

## Target State

New CLI flag `--casting` produces:
```
python fingerprint_displace.py designs/PDG040.3dm fingerprint.png --casting
```

Output:
- `output/PDG040_casting.stl` — single closed mesh: metal body + fingerprint zones merged (millimeters, Rhino coordinate system)
- `output/PDG040_casting.3dm` — same mesh in Rhino format for designer inspection
- Per-zone STLs still generated (unchanged, for web preview)

## Architecture: Hybrid Approach (pluggable mesher + Python surgery)

### Mesher Architecture

The body meshing step is a **pluggable dependency** with two implementations:

1. **Primary: Python UV-sampling mesher** — runs anywhere (CI, server, headless). Uses the existing UV-sampling technique from `pipeline.py:_mesh_brep_face()` to mesh each Brep face. Quality is good for most jewelry geometry. All pytest tests use this path.

2. **Optional upgrade: Rhino MCP mesher** — activated with `--rhino-mesh` flag. Uses Rhino's NURBS mesher for superior quality on complex curved geometry. Requires Rhino 8 running with MCP server.

Both meshers produce a `trimesh.Trimesh` object (see Dependencies section). All downstream steps (hole cutting, stitching, validation) are mesher-agnostic.

### Step 1: Mesh the body

Convert the original Brep body objects into a single triangle mesh.

**Object classification** — what gets meshed:
- Include: Breps and Extrusions on metal layers (body, settings, prongs, bezels, bail/loop)
- Exclude: InstanceReferences where definition name contains "Diamond", "Gem", "Stone", "Brilliant", or layer name contains "diamond", "gem", "stone" (case-insensitive). Note: "round" alone is too generic — only match compound names like "Diamond_Round".
- Exclude: TextDots, Curves, Points, PointClouds
- Exclude: FACE-layer objects (zone surfaces used only for displacement mapping)

**Python mesher path** (primary):
- For each included Brep, iterate faces and UV-sample each face into a triangle mesh
- Resolution: match the `--resolution` parameter (default 250) for consistency
- Combine all face meshes into one `trimesh.Trimesh`
- Merge duplicate vertices at Brep face boundaries (same spatial hash welding we already use)

**Rhino MCP mesher path** (optional):
- Open original .3dm in Rhino via MCP
- Select metal body objects (using classification rules above)
- Run `_Mesh` with jewelry-grade settings: MaxEdgeLength=0.1mm, MinEdgeLength=0.01mm, MaxAngle=15deg
- Join meshes, export as STL, load into `trimesh.Trimesh`

### Step 2: Cut zone holes in body mesh (Python + trimesh)

For each fingerprint zone, remove body mesh triangles that fall within the zone area.

**Algorithm — 3D surface-projected containment test**:

The zone boundary is defined in 3D on the FACE surface. For curved surfaces (P246 teardrop, AAP10985F dome), a simple XY projection is lossy. Instead:

1. Get the zone boundary as 3D points on the FACE surface. Note: `extract_trim_boundary` currently returns 2D `(X, Y)` tuples — it must be extended to also return `(X, Y, Z)` triples (or a `_3d` variant created) for 3D surface-projected containment to work.
2. Project each body mesh triangle centroid onto the FACE surface using closest-point projection (find the nearest point on the FACE surface to the centroid)
3. Test if that projected point falls within the zone's UV-space trim boundary
4. **Z-depth disambiguation**: For designs where zones exist on opposite sides (AAP10985F: Zone 1 on front, Zones 2+3 on back), check the surface normal direction at the projected point. Only cut triangles whose normal is roughly aligned with the zone's FACE normal (dot product > 0.5). This prevents a front-side zone from cutting back-side triangles.

**Boundary triangle handling**:
- Triangles fully inside: remove
- Triangles fully outside: keep
- Triangles straddling the boundary: **clip** using 2D projected approach:
  1. Project both the triangle and zone boundary onto a local tangent plane (or the FACE's UV space)
  2. Use `shapely` (2D polygon clipping) to compute the triangle-minus-zone-interior
  3. Triangulate the remaining polygon fragments and back-project to 3D
  4. If clipping fails for a specific triangle (degenerate geometry), fall back to "remove if any vertex inside" for that triangle only
- This produces a clean hole edge that closely follows the zone boundary, rather than a ragged staircase.

**Body mesh repair after hole cutting**:
- The Python UV-sampler may produce small gaps at Brep face seam boundaries. After cutting holes, run `trimesh.repair.fill_holes()` on the body mesh to seal any pre-existing micro-gaps before stitching.

Result: body mesh with clean holes matching each zone's shape.

### Step 3: Stitch displacement mesh to body (Python)

For each zone, connect the displacement mesh (front face only — the displaced surface) to the body mesh hole.

**Stitching algorithm — "Zipper" with resampling**:

1. **Extract boundary loops**:
   - Body hole boundary: extract edges shared by exactly 1 triangle (boundary edges), order into a connected loop. If multiple disconnected loops result (shouldn't happen with proper clipping), take the largest.
   - Zone displacement mesh boundary: extract boundary edges, order into a connected loop. Note: this loop follows the UV grid staircase pattern.

2. **Resample both loops to matching density**:
   - Compute arc-length of both loops
   - Resample both to N evenly-spaced points where N = max(len(body_loop), len(zone_loop))
   - This ensures 1:1 vertex correspondence for clean zipping

3. **Zip the loops**:
   - Align the two resampled loops: find the rotation offset that minimizes total distance between corresponding point pairs
   - For each pair of adjacent vertices on loop A (a0, a1) and corresponding pair on loop B (b0, b1), create two triangles: (a0, b0, b1) and (a0, b1, a1)
   - This produces a clean quad strip (as pairs of triangles) bridging the two boundaries

4. **Orient normals consistently**:
   - Compute the stitching strip normal for each triangle
   - Compare to the average of neighboring body mesh / zone mesh normals
   - Flip winding if needed to maintain outward-facing normals throughout

**Result**: body mesh + zone meshes + bridge strips form a single connected mesh.

### Step 4: Validate and export (Python + trimesh)

Validation checks (all must pass for `--casting` to produce output):

1. **Closed mesh**: `trimesh.is_watertight` — every edge shared by exactly 2 triangles
2. **Manifold**: no edge shared by more than 2 triangles (`trimesh.is_volume`)
3. **Consistent normals**: `trimesh.fix_normals()` — auto-fix, then verify with winding check
4. **No degenerate triangles**: filter triangles with area < 1e-10 mm^2
5. **Self-intersection check**: Build a spatial index (`scipy.spatial.cKDTree`) of triangle centroids near stitch boundaries (within 0.5mm). For each triangle in this zone, query neighbors and test pairwise triangle-triangle intersection. This is targeted (only checks stitch-boundary vicinity), not exhaustive O(n^2). If intersections found, attempt local remeshing via `trimesh.repair.fix_inversion()` or remove offending triangles and re-fill.
6. **Wall thickness**: cast 500 rays from random surface points inward along the inverted normal. Measure distance to the opposite surface. Minimum must be >= 0.75mm. Warn (don't abort) if 0.5-0.75mm detected.
7. **Zero spill**: for each zone, project every displacement vertex onto the FACE surface (closest-point projection) and test UV-space containment in the zone trim boundary — same 3D approach used in Step 2 for hole cutting. This handles curved surfaces correctly (XY projection is lossy for curved zones like P246).
8. **File size**: warn if > 50MB, suggest `--resolution` reduction.

**Failure behavior**:
- If validation fails on a specific zone (stitching gap, spill), **skip that zone** and produce a partial result with a clear warning listing which zones succeeded and which failed.
- If ALL zones fail, abort with error.
- Never produce a silently broken file.

**P246 Zone 2 special case**: This zone is 0.2mm thick — below the 0.75mm wall thickness threshold. The pipeline will process it but emit a warning: "Zone 2: wall thickness 0.2mm is below casting minimum (0.75mm). Fingerprint depth auto-clamped to 0.1mm." This already happens in the current pipeline (the depth clamping). The casting validation will flag it as a warning, not an error.

Export:
- Binary STL in millimeters (same format as current `export_stl()`)
- Also save as .3dm mesh object on a `CASTING_MERGED` layer for designer inspection

### Relationship to existing `watertight` parameter

The existing `watertight=True` mode in `build_displaced_mesh` creates a self-contained closed shell per zone (front + back + sidewalls). This is used for per-zone STL export and web preview. The casting pipeline does NOT use these watertight shells — it uses only the **front face** (display mesh, `watertight=False`) from each zone, because the "back" of the zone in the casting mesh is the body itself. The watertight mode remains unchanged and continues to serve the per-zone STL / web preview path.

## Object Classification

How to identify what's metal body vs gems vs other:

### General rule
- Include: Breps/Extrusions (the metal body, settings, bail)
- Exclude: InstanceReferences whose definition name matches `/(diamond|gem|stone|brilliant)/i` OR whose layer name matches `/(diamond|gem|stone)/i` (case-insensitive). Note: "round" alone is too generic — only match `diamond_round` or similar compound names.
- Exclude: TextDots, Curves, Points, Annotations
- Exclude: Objects on layers matching `FP_ZONE_*_FACE` (zone surfaces, not metal)

### Design-specific notes

**PDG040** (no gems): All objects on BODY/GRUE METAL/LOOP layers = metal body. FACE layers = zone surfaces (exclude from body mesh).

**P246** (26 gems): Default layer Breps = metal body. Diamond_Round InstanceReferences = gem stones (exclude). FP_ZONE_N_FACE/BODY layers for zone identification.

**AAP10985F** (48 gems): Metal layers (Metal 01-06, Mains, etc.) = metal body. Setting layers = metal (include). InstanceReferences on gem/diamond layers = gem stones (exclude).

## Boundary Containment (Zero Spill)

The displacement mesh must not extend beyond zone boundaries. Enforced at multiple levels:

1. **Grid generation**: UV grid is clipped to zone boundary via point-in-polygon test (existing)
2. **Feather**: Displacement fades to zero at edges (existing, configurable via `--feather-mm`)
3. **Hole clipping**: Body mesh triangles are clipped precisely at the zone boundary, not ragged-cut
4. **Stitching**: Bridge strip connects zone boundary to body hole boundary — geometry stays within zone
5. **Post-merge validation**: Every displacement vertex projected onto FACE surface must test inside zone trim boundary (3D projected, not XY)

## Testing Plan

### Programmatic Tests (pytest, no Rhino required)

All tests use the Python UV-sampling mesher (primary path):

- `test_body_mesh_creation`: Python mesher produces valid closed mesh from Brep
- `test_gem_exclusion`: InstanceReferences with Diamond/Gem names excluded from body mesh
- `test_zone_hole_cutting`: Correct triangles removed, hole boundary follows zone shape
- `test_z_depth_disambiguation`: AAP10985F front zone doesn't cut back-side triangles
- `test_boundary_clipping`: Straddling triangles clipped cleanly (no ragged edges)
- `test_boundary_stitching`: Bridge strip is watertight, consistent normals
- `test_merged_mesh_closed`: Final mesh `is_watertight` returns True
- `test_merged_mesh_manifold`: No non-manifold edges
- `test_no_degenerate_tris`: Zero degenerate triangles in output
- `test_wall_thickness`: Min thickness >= 0.75mm at sample points (or warning for known thin zones)
- `test_zero_spill`: No displacement vertex outside zone boundary
- `test_normal_consistency`: All normals point outward
- `test_partial_failure`: If one zone fails, others still produce output with warning
- `test_all_designs`: Full casting pipeline on PDG040, P246, AAP10985F

### Visual Verification (Rhino MCP)

For each design:
1. Import casting STL into Rhino
2. Rendered view from multiple angles — fingerprint ridges visible and crisp
3. Section analysis — cut through zone to verify wall thickness
4. Wireframe view — verify mesh continuity at stitch boundaries
5. Edge analysis — verify no naked (boundary) edges

### Stakeholder Validation

**As Subroto/Reeta (designer)**:
- Open output .3dm — design looks correct
- Gem settings intact, not covered by fingerprint
- Zone boundaries clean, no overlap or spill
- Wall thickness ≥ 0.75mm

**As caster**:
- Import STL into slicer
- Single closed mesh, no import errors
- No self-intersections or inverted normals
- File size < 50MB
- Printable wall thickness throughout

**As final user**:
- Fingerprint ridges visible and tactile
- No sharp edges that catch
- Piece looks premium, matches original design
- Fingerprint recognizable as a real fingerprint

## File Changes

- `3dm files/fingerprint_displace.py` — add `--casting` flag to CLI, extend `extract_trim_boundary` to return 3D points (add Z coordinate), wire up casting merge step in `main()`
- `3dm files/casting_merge.py` — new module: body meshing (pluggable), gem exclusion logic, hole cutting, boundary clipping, stitching, validation, merged STL export
- `3dm files/tests/test_casting.py` — new test file for casting pipeline
- `environment.yml` or conda env — add `trimesh` and `shapely` dependencies
- No changes to `backend/preview/pipeline.py` (web preview unchanged)

## Dependencies

- **New**: `trimesh` — mesh processing library for watertight validation, normal fixing, ray casting, hole repair. Well-maintained, MIT licensed, pure Python with optional C speedups.
- **New**: `shapely` — 2D polygon clipping for boundary triangle handling (used by trimesh internally too). Well-maintained, BSD licensed.
- **Existing**: `rhino3dm`, `numpy`, `pillow`, `scipy`
- **Optional**: Rhino 8 + MCP server (for `--rhino-mesh` upgrade path)

## Risks

1. **Boundary stitching quality**: The body mesh and zone mesh have different vertex densities at the boundary. Mitigation: resample both boundary loops to matching density before zipping.

2. **Z-depth disambiguation**: AAP10985F has zones on front and back. Mitigation: normal-direction check prevents cross-side cutting.

3. **Complex geometry near zone edges**: Gem settings near zone boundaries could create thin/fragile geometry. Mitigation: wall thickness validation catches this; warn user if detected.

4. **Rhino MCP reliability**: Mitigation: Python mesher is the primary path. Rhino is optional upgrade only.

5. **Large file sizes**: High-resolution body mesh + displacement = potentially large STL. Mitigation: if file exceeds 50MB, suggest reducing `--resolution`. Future: add `--decimate` flag that reduces body mesh triangles far from zone boundaries while preserving fingerprint detail.

6. **Triangle clipping complexity**: Splitting triangles at zone boundaries requires robust geometric intersection code. Mitigation: use `shapely` for 2D projected clipping; if clipping fails on a specific triangle, fall back to the "remove if any vertex inside" heuristic for that triangle only.

7. **Body mesh from Python UV-sampler may not be watertight**: UV-sampled face meshes can have micro-gaps at Brep face seam boundaries where parameterizations don't align. Mitigation: run `trimesh.repair.fill_holes()` after body meshing and before hole cutting. If gaps are too large, warn and fall back to the Rhino mesher path.
