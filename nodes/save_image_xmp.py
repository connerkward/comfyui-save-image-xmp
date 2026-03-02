import hashlib
import io
import json
import os
import re
import struct
import zlib
from xml.sax.saxutils import escape

import folder_paths
from PIL import Image, PngImagePlugin


# --- Model hash collection (shared cache across all save nodes) ---

_hash_cache: dict[str, str] = {}


def _sha256(path: str) -> str:
    if path in _hash_cache:
        return _hash_cache[path]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    _hash_cache[path] = h.hexdigest()
    return _hash_cache[path]


def _resolve(value: str) -> str | None:
    for folder_type in folder_paths.folder_names_and_paths:
        path = folder_paths.get_full_path(folder_type, value)
        if path and os.path.isfile(path):
            return path
    normalized = re.sub(r'\s*\([^)]*\)\s*$', '', value).lower()
    models_dir = folder_paths.models_dir
    search_dirs = set()
    for bases, _ in folder_paths.folder_names_and_paths.values():
        search_dirs.update(bases)
    if os.path.isdir(models_dir):
        for name in os.listdir(models_dir):
            d = os.path.join(models_dir, name)
            if os.path.isdir(d):
                search_dirs.add(d)
    for base in search_dirs:
        try:
            for fname in os.listdir(base):
                stem = os.path.splitext(fname)[0]
                if stem == value or stem.lower() == normalized:
                    full = os.path.join(base, fname)
                    if os.path.isfile(full):
                        return full
        except OSError:
            continue
    return None


def _collect_model_hashes(prompt: dict) -> str:
    results, seen = [], set()
    if not prompt:
        return "[]"
    for node in prompt.values():
        for value in node.get("inputs", {}).values():
            if not isinstance(value, str) or not value or len(value) > 260 or value.startswith("http"):
                continue
            full_path = _resolve(value)
            if not full_path or full_path in seen:
                continue
            seen.add(full_path)
            try:
                digest = _sha256(full_path)
            except OSError:
                digest = ""
            results.append({"name": value, "path": full_path, "sha256": digest})
    return json.dumps(results)


# --- XMP / file helpers ---

def _build_xmp(workflow: str, prompt: str, models: str, extra: str, layers: str = "", author: str = "") -> str:
    try:
        model_list = json.loads(models) if models else []
        model_names = ", ".join(m["name"] for m in model_list if "name" in m)
    except (json.JSONDecodeError, TypeError):
        model_names = ""

    xmp = (
        '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '    <rdf:Description rdf:about=""\n'
        '      xmlns:cfl="https://github.com/connerkward/comfyui-save-image-xmp/ns/v1">\n'
        f"      <cfl:workflow>{escape(str(workflow))}</cfl:workflow>\n"
        f"      <cfl:prompt>{escape(str(prompt))}</cfl:prompt>\n"
        f"      <cfl:models>{escape(str(models))}</cfl:models>\n"
        f"      <cfl:extra>{escape(str(extra))}</cfl:extra>\n"
    )
    if author:
        xmp += f"      <cfl:author>{escape(str(author))}</cfl:author>\n"
    if layers:
        xmp += f"      <cfl:layers>{escape(str(layers))}</cfl:layers>\n"
    xmp += "    </rdf:Description>\n"

    # Dublin Core — visible in Mac Get Info / Windows Properties
    xmp += '    <rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
    if author:
        xmp += (
            "      <dc:creator><rdf:Seq>"
            f"<rdf:li>{escape(str(author))}</rdf:li>"
            "</rdf:Seq></dc:creator>\n"
        )
    if model_names:
        xmp += (
            "      <dc:description><rdf:Alt>"
            f'<rdf:li xml:lang="x-default">{escape(model_names)}</rdf:li>'
            "</rdf:Alt></dc:description>\n"
        )
    xmp += "    </rdf:Description>\n"

    xmp += (
        "  </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        '<?xpacket end="w"?>'
    )
    return xmp


def _next_filename(output_dir: str, prefix: str, ext: str) -> str:
    counter = 1
    while True:
        name = f"{prefix}_{counter:05d}.{ext}"
        path = os.path.join(output_dir, name)
        if not os.path.exists(path):
            return path
        counter += 1


def _tensor_to_pil(tensor):
    arr = (tensor.cpu().numpy() * 255).clip(0, 255).astype("uint8")
    return Image.fromarray(arr)


def _save_png(pil: Image.Image, path: str, xmp_str: str, workflow: str, prompt: str):
    pnginfo = PngImagePlugin.PngInfo()
    if workflow:
        pnginfo.add_text("workflow", workflow)
    if prompt:
        pnginfo.add_text("prompt", prompt)
    pnginfo.add_itxt("XML:com.adobe.xmp", xmp_str)
    pil.save(path, format="PNG", pnginfo=pnginfo)


def _save_webp(pil: Image.Image, path: str, xmp_bytes: bytes, quality: int):
    pil.save(path, format="WEBP", xmp=xmp_bytes, quality=quality)


def _save_jpeg(pil: Image.Image, path: str, xmp_bytes: bytes, quality: int):
    buf = io.BytesIO()
    pil.save(buf, format="JPEG", quality=quality)
    jpeg = buf.getvalue()
    marker_data = b"http://ns.adobe.com/xap/1.0/\x00" + xmp_bytes
    seg_len = len(marker_data) + 2
    app1 = b"\xff\xe1" + struct.pack(">H", seg_len) + marker_data
    final = jpeg[:2] + app1 + jpeg[2:]
    with open(path, "wb") as f:
        f.write(final)


class SaveImageXMP:
    CATEGORY = "image"
    OUTPUT_NODE = True
    RETURN_TYPES = ()
    FUNCTION = "save"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "ComfyUI-XMP"}),
                "author": ("STRING", {"default": ""}),
                "format": (["PNG", "WEBP", "JPEG"],),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
            },
            "optional": {
                "json_metadata": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def save(
        self,
        images,
        filename_prefix="ComfyUI-XMP",
        author="",
        format="PNG",
        quality=95,
        json_metadata=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        output_dir = folder_paths.get_output_directory()
        ext = format.lower()

        workflow_str = ""
        if extra_pnginfo and "workflow" in extra_pnginfo:
            workflow_str = json.dumps(extra_pnginfo["workflow"])

        prompt_str = json.dumps(prompt) if prompt else ""
        models_str = _collect_model_hashes(prompt)
        extra_str = json_metadata if json_metadata else "{}"

        results = []
        for tensor in images:
            pil = _tensor_to_pil(tensor)
            xmp_str = _build_xmp(workflow_str, prompt_str, models_str, extra_str, author=author)
            xmp_bytes = xmp_str.encode("utf-8")
            path = _next_filename(output_dir, filename_prefix, ext)

            if format == "PNG":
                _save_png(pil, path, xmp_str, workflow_str, prompt_str)
            elif format == "WEBP":
                _save_webp(pil, path, xmp_bytes, quality)
            elif format == "JPEG":
                _save_jpeg(pil, path, xmp_bytes, quality)

            results.append({"filename": os.path.basename(path), "subfolder": "", "type": "output"})

        return {"ui": {"images": results}}
