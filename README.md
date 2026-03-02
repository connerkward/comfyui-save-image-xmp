# ComfyUI Save Layered Image with Metadata!

ComfyUI custom nodes for saving LAYERED images with embedded XMP metadata — workflow, prompt graph, model SHA256 hashes, and arbitrary JSON, all burned into the file.

---

## Save Image (XMP)

![Save Image (XMP)](screenshots/save-image-xmp.png)

Saves a single image as **PNG**, **WEBP**, or **JPEG** with XMP metadata embedded inline.

| Input | Type | Description |
|---|---|---|
| `images` | IMAGE | Image batch to save |
| `json_metadata` | STRING | Optional JSON to embed in `cfl:extra` |
| `filename_prefix` | STRING | Output filename prefix |
| `author` | STRING | Author name embedded in XMP |
| `format` | PNG/WEBP/JPEG | Output format |
| `quality` | INT | Quality for lossy formats (1–100) |

PNG files also get `workflow` and `prompt` tEXt chunks for native ComfyUI workflow reload.

---

## Save Layered TIFF (XMP)

![Save Layered TIFF (XMP)](screenshots/save-layered-tiff-xmp.png)

Saves a multi-page TIFF where each page is a named layer. XMP metadata is embedded on page 0. Previews all layers in the node UI.

| Input | Type | Description |
|---|---|---|
| `preview_image` | IMAGE | Page 0 / thumbnail layer |
| `layers` | IMAGE | Additional layers (list) |
| `layer_names` | STRING | Names aligned to `layers` (list) |
| `json_metadata` | STRING | Optional JSON to embed in `cfl:extra` |
| `preview_name` | STRING | Name for the preview layer |
| `filename_prefix` | STRING | Output filename prefix |
| `author` | STRING | Author name embedded in XMP |

Returns the output `filepath` as a STRING for downstream nodes.

> macOS QuickLook, Finder thumbnails, and Preview.app all render the TIFF natively (Deflate/ZIP compression).

---

## XMP fields

All saved files embed a custom XMP block:

| Field | Content |
|---|---|
| `cfl:workflow` | Full ComfyUI node graph JSON |
| `cfl:prompt` | Execution prompt graph JSON |
| `cfl:models` | SHA256 hashes of all model files used |
| `cfl:extra` | Arbitrary JSON from `json_metadata` input |
| `cfl:author` | Author string |
| `cfl:layers` | Comma-separated layer names (TIFF only) |

Model hashes are collected automatically from the run graph and cached per session.

---

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/connerkward/comfyui-save-image-xmp.git
pip install tifffile
```

Or via ComfyUI Manager: search `comfyui-save-image-xmp`.
