# Bobo & Musu — Fingerprint Jewelry Preview (MVP Guide)

## What It Does

This tool lets you preview how a fingerprint will look embossed onto a custom jewelry piece — before it goes to production. Upload a fingerprint image, pick a design and zones, and see a photorealistic 3D preview rendered in your browser.

---

## Getting Started

### 1. Start the Server

```bash
conda activate bobomusu
cd backend
python manage.py runserver 0.0.0.0:8000
```

Open **http://localhost:8000** in your browser.

---

## Walkthrough

### Step 1: Upload a Fingerprint

- Click the **drop zone** or drag-and-drop an image file (PNG, JPG, BMP, or TIFF).
- A small preview of your fingerprint appears in the sidebar.
- Maximum file size: 10 MB.
- Click the **x** button to clear and upload a different image.

### Step 2: Select a Design

- Use the **Design** dropdown to choose a jewelry piece.
- The 3D model loads automatically in the viewport. You can orbit, zoom, and pan using your mouse:
  - **Left-click drag** — orbit / rotate
  - **Scroll wheel** — zoom in/out
  - **Right-click drag** — pan

### Step 3: Choose Zones

- Each design has numbered **zones** — the areas where the fingerprint can be applied.
- Check or uncheck zones to control which surfaces get the fingerprint.
- All zones are selected by default.

### Step 4: Unified Mapping (Optional)

- **Off** (default): Each zone gets its own independent copy of the fingerprint, scaled to fit that zone.
- **On**: One single fingerprint is mapped continuously across all selected zones. This creates a seamless look when zones are adjacent.

### Step 5: Adjust Intensity

- Use the **Fingerprint Intensity** slider to control how pronounced the fingerprint ridges appear.
- **Subtle** = shallow, delicate engraving. **Bold** = deep, prominent ridges.
- The default is a balanced middle value. Experiment to find the right look.

### Step 6: Generate Preview

- Click **Generate Preview** to process the fingerprint.
- Processing takes 10–45 seconds depending on how many zones are selected.
- The displaced fingerprint zones appear overlaid on the base jewelry model.

---

## Available Designs

| Design | Zones | Description |
|--------|-------|-------------|
| **Pendant — 5 Zone** (PDG040) | 5 | Pendant with 5 triangular fingerprint zones forming the body |
| **Pendant — 2 Zone** (P246) | 2 | Teardrop pendant with 2 curved fingerprint zones |

---

## Tips

- **Higher zone count = longer processing.** 5 zones takes roughly 2–3x longer than 2 zones.
- **Unified mapping works best** when selecting adjacent zones on the same face of the piece.
- The 3D preview uses the same coordinate system as the manufacturing pipeline — what you see is what gets produced.
- The viewport renders in real-time WebGL with physically-based materials (metallic gold with environment reflections).

---

## Technical Notes

- **Backend**: Django + Django REST Framework. The displacement pipeline uses `rhino3dm` for geometry and NumPy for mesh operations.
- **Frontend**: Three.js with `MeshPhysicalMaterial` for photorealistic gold rendering. Base meshes are pre-exported as GLB (binary glTF) for fast loading.
- **Pipeline**: Fingerprint images are preprocessed (grayscale, contrast-enhanced), then mapped onto zone surfaces as height displacement. Output is binary STL per zone.
