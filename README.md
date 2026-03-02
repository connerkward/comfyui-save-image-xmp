# comfyui-save-image-xmp

ComfyUI custom nodes for saving images with embedded XMP metadata.

## Nodes

### Save Image (XMP)
Saves images as PNG, WebP, or JPEG with XMP metadata embedded using namespace:
`xmlns:cfl="http://ns.conward.io/comfyui/1.0/"`

Fields written: `cfl:workflow`, `cfl:prompt`, `cfl:models`, `cfl:extra`

Inputs:
- `images` — IMAGE
- `filename_prefix` — output filename prefix
- `format` — PNG / WEBP / JPEG
- `quality` — 1–100 (lossy formats only)
- `models` — JSON string (optional, wire from Model Hash Collector)
- `extra_metadata` — JSON string (optional, corp formatter nodes)

### Model Hash Collector
Reads the current prompt graph, finds all model loader nodes, resolves file paths,
computes SHA256 hashes (cached per session), and outputs a JSON array:
`[{"name": "...", "path": "...", "sha256": "..."}]`

Wire output → `Save Image (XMP).models`
