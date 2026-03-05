import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";

// ── DOM refs ──
const designSelect = document.getElementById("design-select");
const zonesContainer = document.getElementById("zones-container");
const generateBtn = document.getElementById("generate-btn");
const statusBar = document.getElementById("status-bar");
const spinner = document.getElementById("spinner");
const statusText = document.getElementById("status-text");
const errorBar = document.getElementById("error-bar");
const fpInput = document.getElementById("fingerprint-input");
const dropZone = document.getElementById("drop-zone");
const fpPreviewContainer = document.getElementById("fp-preview-container");
const fpPreviewImg = document.getElementById("fp-preview");
const fpClear = document.getElementById("fp-clear");
const unifiedCheck = document.getElementById("unified-check");
const intensitySlider = document.getElementById("intensity-slider");
const canvas = document.getElementById("viewer-canvas");
const statsEl = document.getElementById("stats");

let fingerprintFile = null;
let designs = [];

// ── Three.js setup ──
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.4;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();

// Premium gradient background — warm taupe studio backdrop
{
    const bgCanvas = document.createElement("canvas");
    bgCanvas.width = 1024;
    bgCanvas.height = 1024;
    const ctx = bgCanvas.getContext("2d");

    // Base: warm mid-gray
    ctx.fillStyle = "#3d3a42";
    ctx.fillRect(0, 0, 1024, 1024);

    // Bright warm center — studio spotlight feel
    const spotlight = ctx.createRadialGradient(512, 460, 0, 512, 460, 550);
    spotlight.addColorStop(0, "rgba(120, 110, 105, 0.6)");
    spotlight.addColorStop(0.3, "rgba(90, 82, 80, 0.4)");
    spotlight.addColorStop(0.65, "rgba(65, 60, 66, 0.15)");
    spotlight.addColorStop(1, "rgba(50, 46, 54, 0)");
    ctx.fillStyle = spotlight;
    ctx.fillRect(0, 0, 1024, 1024);

    // Vignette — darken edges for depth
    const vignette = ctx.createRadialGradient(512, 512, 250, 512, 512, 720);
    vignette.addColorStop(0, "rgba(0, 0, 0, 0)");
    vignette.addColorStop(0.7, "rgba(0, 0, 0, 0.08)");
    vignette.addColorStop(1, "rgba(0, 0, 0, 0.25)");
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, 1024, 1024);

    const bgTexture = new THREE.CanvasTexture(bgCanvas);
    bgTexture.colorSpace = THREE.SRGBColorSpace;
    scene.background = bgTexture;
}

// Environment map for realistic reflections
const pmremGenerator = new THREE.PMREMGenerator(renderer);
const roomEnv = new RoomEnvironment(renderer);
const envTexture = pmremGenerator.fromScene(roomEnv).texture;
scene.environment = envTexture;
roomEnv.dispose();

const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 500);
camera.position.set(0, -30, 40);

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.1;

// Key light — main specular highlight
const keyLight = new THREE.DirectionalLight(0xffffff, 0.8);
keyLight.position.set(5, -8, 20);
keyLight.castShadow = true;
keyLight.shadow.mapSize.width = 2048;
keyLight.shadow.mapSize.height = 2048;
keyLight.shadow.camera.near = 0.1;
keyLight.shadow.camera.far = 100;
keyLight.shadow.camera.left = -30;
keyLight.shadow.camera.right = 30;
keyLight.shadow.camera.top = 30;
keyLight.shadow.camera.bottom = -30;
keyLight.shadow.bias = -0.001;
scene.add(keyLight);

// Fill light — soften shadows
const fillLight = new THREE.DirectionalLight(0xfff5e6, 0.35);
fillLight.position.set(-8, 6, 10);
scene.add(fillLight);

// Rim light — edge definition
const rimLight = new THREE.DirectionalLight(0xffffff, 0.45);
rimLight.position.set(0, 10, -10);
scene.add(rimLight);

// Ground plane for shadow
const groundGeometry = new THREE.PlaneGeometry(200, 200);
const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.35 });
const ground = new THREE.Mesh(groundGeometry, groundMaterial);
ground.receiveShadow = true;
ground.position.set(0, 0, -1);
scene.add(ground);

// ── Materials ──
// Rich 18k gold — consistent across body and zones for seamless look
const GOLD_PARAMS = {
    color: 0xd4aa40,
    metalness: 1.0,
    roughness: 0.20,
    clearcoat: 0.06,
    clearcoatRoughness: 0.04,
    envMapIntensity: 1.8,
    flatShading: false,
};

const bodyMaterial = new THREE.MeshPhysicalMaterial({ ...GOLD_PARAMS });

// Diamond / gemstone material — metallic mirror approach for small accent stones
const diamondMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    metalness: 0.9,
    roughness: 0.05,
    envMapIntensity: 3.0,
    clearcoat: 1.0,
    clearcoatRoughness: 0.0,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2,
});

function makeZoneMaterial() {
    // Slider controls zone darkness: 0 (subtle) → 1 (bold)
    const raw = parseInt(intensitySlider.value, 10);
    const t = Math.max(0, Math.min(1, (raw - 15) / (55 - 15)));

    // Interpolate from warm gold toward near-black patina
    // Gold: rgb(212, 170, 64)  Dark: rgb(35, 28, 18)
    const r = Math.round(212 - t * 177);
    const g = Math.round(170 - t * 142);
    const b = Math.round(64 - t * 46);
    const color = (r << 16) | (g << 8) | b;

    // Higher intensity = rougher (matte = less specular = darker appearance)
    const roughness = 0.22 + t * 0.45;
    // Higher intensity = much less reflective
    const envIntensity = 1.8 - t * 1.4;

    return new THREE.MeshPhysicalMaterial({
        color: color,
        metalness: 1.0,
        roughness: roughness,
        clearcoat: 0.06,
        clearcoatRoughness: 0.04,
        envMapIntensity: envIntensity,
        flatShading: false,
        polygonOffset: true,
        polygonOffsetFactor: -1,
        polygonOffsetUnits: -1,
    });
}

// ── Scene groups ──
const baseGroup = new THREE.Group();
const gemGroup = new THREE.Group();
const zoneGroup = new THREE.Group();
scene.add(baseGroup);
scene.add(gemGroup);
scene.add(zoneGroup);

function resize() {
    const container = document.getElementById("viewer-container");
    const w = container.clientWidth;
    const h = container.clientHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);
resize();

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();

// ── Helpers ──
function showStatus(msg) {
    statusBar.classList.remove("hidden");
    spinner.classList.remove("hidden");
    statusText.textContent = msg;
    errorBar.classList.add("hidden");
}
function hideStatus() {
    statusBar.classList.add("hidden");
    spinner.classList.add("hidden");
}
function showError(msg) {
    errorBar.classList.remove("hidden");
    errorBar.textContent = msg;
    hideStatus();
}
function clearError() {
    errorBar.classList.add("hidden");
}
function updateGenerateBtn() {
    const hasDesign = designSelect.value !== "";
    const hasZones = zonesContainer.querySelectorAll("input:checked").length > 0;
    const hasFp = fingerprintFile !== null;
    generateBtn.disabled = !(hasDesign && hasZones && hasFp);
}

function disposeGroup(group) {
    while (group.children.length > 0) {
        const child = group.children[0];
        group.remove(child);
        if (child.geometry) child.geometry.dispose();
        if (child.material) child.material.dispose();
    }
}

// ── Mesh loading ──
const stlLoader = new STLLoader();
const objLoader = new OBJLoader();
const gltfLoader = new GLTFLoader();

function loadSTLBuffer(buffer, material, targetGroup) {
    let geometry = stlLoader.parse(buffer);
    geometry = mergeVertices(geometry, 1e-4);
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    targetGroup.add(mesh);
    return geometry.index ? geometry.index.count / 3 : geometry.attributes.position.count / 3;
}

function loadOBJText(text, material, targetGroup) {
    const obj = objLoader.parse(text);
    let totalTris = 0;
    obj.traverse((child) => {
        if (child.isMesh) {
            child.geometry = mergeVertices(child.geometry, 1e-4);
            child.geometry.computeVertexNormals();
            child.material = material;
            child.castShadow = true;
            child.receiveShadow = true;
            totalTris += child.geometry.index
                ? child.geometry.index.count / 3
                : child.geometry.attributes.position.count / 3;
        }
    });
    // Move children into target group
    while (obj.children.length > 0) {
        targetGroup.add(obj.children[0]);
    }
    return totalTris;
}

function loadGLBBuffer(buffer, material, targetGroup) {
    return new Promise((resolve, reject) => {
        gltfLoader.parse(buffer, "", (gltf) => {
            let totalTris = 0;
            gltf.scene.traverse((child) => {
                if (child.isMesh) {
                    child.geometry.computeVertexNormals();
                    child.material = material;
                    child.castShadow = true;
                    child.receiveShadow = true;
                    totalTris += child.geometry.index
                        ? child.geometry.index.count / 3
                        : child.geometry.attributes.position.count / 3;
                }
            });
            while (gltf.scene.children.length > 0) {
                targetGroup.add(gltf.scene.children[0]);
            }
            resolve(totalTris);
        }, (err) => reject(err));
    });
}

function fitCamera() {
    const box = new THREE.Box3().setFromObject(baseGroup);
    if (gemGroup.children.length > 0) {
        box.expandByObject(gemGroup);
    }
    if (zoneGroup.children.length > 0) {
        box.expandByObject(zoneGroup);
    }
    if (box.isEmpty()) return;

    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const dist = maxDim * 2.0;

    // Position ground plane just below the object
    ground.position.set(center.x, center.y, box.min.z - 0.5);

    controls.target.copy(center);
    // Front-facing camera slightly above, looking slightly down — jewelry product shot
    camera.position.set(center.x, center.y - dist * 0.6, center.z + dist * 0.7);
    camera.lookAt(center);
    controls.update();
}

// ── Fingerprint upload ──
dropZone.addEventListener("click", () => fpInput.click());
dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) setFingerprint(e.dataTransfer.files[0]);
});
fpInput.addEventListener("change", () => {
    if (fpInput.files.length > 0) setFingerprint(fpInput.files[0]);
});
fpClear.addEventListener("click", () => {
    fingerprintFile = null;
    fpPreviewContainer.classList.add("hidden");
    dropZone.style.display = "";
    fpInput.value = "";
    updateGenerateBtn();
});

function setFingerprint(file) {
    if (!file.type.startsWith("image/")) {
        showError("Please upload an image file (PNG, JPG, BMP, TIFF)");
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showError("File too large. Maximum size is 10MB.");
        return;
    }
    fingerprintFile = file;
    const url = URL.createObjectURL(file);
    fpPreviewImg.src = url;
    fpPreviewContainer.classList.remove("hidden");
    dropZone.style.display = "none";
    clearError();
    updateGenerateBtn();
}

// ── Load designs ──
async function loadDesigns() {
    try {
        const resp = await fetch("/api/designs/");
        const data = await resp.json();
        designs = data.designs;
        designSelect.innerHTML = '<option value="">Select a design...</option>';
        for (const d of designs) {
            const opt = document.createElement("option");
            opt.value = d.id;
            opt.textContent = `${d.display_name} (${d.zones.length} zones)`;
            designSelect.appendChild(opt);
        }
    } catch (err) {
        showError("Failed to load designs: " + err.message);
    }
}

// ── Load base mesh when design is selected ──
designSelect.addEventListener("change", async () => {
    const id = designSelect.value;
    const design = designs.find((d) => d.id === id);

    // Update zone checkboxes
    zonesContainer.innerHTML = "";
    if (design) {
        for (const z of design.zones) {
            const lbl = document.createElement("label");
            lbl.innerHTML = `<input type="checkbox" value="${z}" checked> Zone ${z}`;
            lbl.querySelector("input").addEventListener("change", updateGenerateBtn);
            zonesContainer.appendChild(lbl);
        }
    }
    updateGenerateBtn();

    // Clear previous scene
    disposeGroup(baseGroup);
    disposeGroup(gemGroup);
    disposeGroup(zoneGroup);
    statsEl.textContent = "";

    if (!id) return;

    // Fetch and display base mesh — try GLB (fast, small) then fall back to OBJ
    showStatus("Loading design...");
    try {
        let tris = 0;
        const glbResp = await fetch(`/static/meshes/${id}_base.glb`);
        if (glbResp.ok) {
            const buffer = await glbResp.arrayBuffer();
            tris = await loadGLBBuffer(buffer, bodyMaterial, baseGroup);
        } else {
            // Fallback to OBJ via API
            const resp = await fetch(`/api/designs/${id}/mesh/`);
            if (!resp.ok) {
                showError("Failed to load design mesh");
                return;
            }
            const objText = await resp.text();
            tris = loadOBJText(objText, bodyMaterial, baseGroup);
        }

        // Load gems if design has them
        let gemTris = 0;
        if (design.has_gems) {
            try {
                const gemResp = await fetch(`/static/meshes/${id}_gems.glb`);
                if (gemResp.ok) {
                    const gemBuf = await gemResp.arrayBuffer();
                    gemTris = await loadGLBBuffer(gemBuf, diamondMaterial, gemGroup);
                }
            } catch (_) { /* gems are optional */ }
        }

        fitCamera();
        hideStatus();
        const gemText = gemTris > 0 ? ` | Gems: ${gemTris.toLocaleString()}` : "";
        statsEl.textContent = `Base mesh: ${tris.toLocaleString()}${gemText} triangles`;
    } catch (err) {
        showError("Failed to load design mesh: " + err.message);
    }
});

// ── Generate preview ──
generateBtn.addEventListener("click", generatePreview);

async function generatePreview() {
    clearError();
    const designId = designSelect.value;
    const checkedZones = [...zonesContainer.querySelectorAll("input:checked")].map((cb) => cb.value);
    const mode = "emboss";
    const unified = unifiedCheck.checked;

    if (!designId || checkedZones.length === 0 || !fingerprintFile) return;

    const formData = new FormData();
    formData.append("fingerprint", fingerprintFile);
    formData.append("design_id", designId);
    formData.append("zones", checkedZones.join(","));
    formData.append("mode", mode);
    if (unified) formData.append("unified", "true");

    generateBtn.disabled = true;
    showStatus("Processing fingerprint...");
    const t0 = performance.now();

    try {
        const resp = await fetch("/api/preview/", { method: "POST", body: formData });
        const elapsed = ((performance.now() - t0) / 1000).toFixed(1);

        if (!resp.ok) {
            let errMsg;
            try {
                const errData = await resp.json();
                errMsg = errData.error || errData.detail || "Request failed";
            } catch {
                errMsg = `Server error (${resp.status})`;
            }
            showError(errMsg);
            return;
        }

        // Clear previous zone meshes only (keep base)
        disposeGroup(zoneGroup);

        const contentType = resp.headers.get("Content-Type") || "";
        let totalTriangles = 0;
        let zoneCount = 0;

        if (contentType.includes("application/octet-stream")) {
            const buffer = await resp.arrayBuffer();
            totalTriangles += loadSTLBuffer(buffer, makeZoneMaterial(), zoneGroup);
            zoneCount = 1;
        } else {
            const data = await resp.json();
            for (const [zoneKey, zoneData] of Object.entries(data.zones)) {
                const binary = atob(zoneData.stl_base64);
                const buffer = new ArrayBuffer(binary.length);
                const view = new Uint8Array(buffer);
                for (let i = 0; i < binary.length; i++) view[i] = binary.charCodeAt(i);
                totalTriangles += loadSTLBuffer(buffer, makeZoneMaterial(), zoneGroup);
                zoneCount++;
            }
        }

        fitCamera();
        hideStatus();

        let baseTris = 0;
        baseGroup.traverse((child) => {
            if (child.isMesh) baseTris += child.geometry.index ? child.geometry.index.count / 3 : child.geometry.attributes.position.count / 3;
        });

        statsEl.textContent = `Pipeline: ${elapsed}s | Base: ${baseTris.toLocaleString()} | Zones: ${totalTriangles.toLocaleString()} (${zoneCount}) | Total: ${(baseTris + totalTriangles).toLocaleString()} triangles`;
    } catch (err) {
        showError("Request failed: " + err.message);
    } finally {
        updateGenerateBtn();
    }
}

// ── Intensity slider: live-update zone material without re-running pipeline ──
intensitySlider.addEventListener("input", () => {
    if (zoneGroup.children.length === 0) return;
    const mat = makeZoneMaterial();
    zoneGroup.traverse((child) => {
        if (child.isMesh) {
            if (child.material) child.material.dispose();
            child.material = mat;
        }
    });
});

// ── Init ──
loadDesigns();
