import io
import json
import os
import struct
import zlib
from xml.sax.saxutils import escape

import folder_paths
from PIL import Image, PngImagePlugin


def _build_xmp(workflow: str, prompt: str, models: str, extra: str, layers: str = "") -> str:
    xmp = (
        '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '    <rdf:Description rdf:about=""\n'
        '      xmlns:cfl="http://ns.conward.io/comfyui/1.0/">\n'
        f"      <cfl:workflow>{escape(workflow)}</cfl:workflow>\n"
        f"      <cfl:prompt>{escape(prompt)}</cfl:prompt>\n"
        f"      <cfl:models>{escape(models)}</cfl:models>\n"
        f"      <cfl:extra>{escape(extra)}</cfl:extra>\n"
    )
    if layers:
        xmp += f"      <cfl:layers>{escape(layers)}</cfl:layers>\n"
    xmp += (
        "    </rdf:Description>\n"
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
    # APP1 segment: FF E1, 2-byte big-endian length (includes length field itself)
    seg_len = len(marker_data) + 2
    app1 = b"\xff\xe1" + struct.pack(">H", seg_len) + marker_data

    # Insert after SOI (first 2 bytes)
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
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "format": (["PNG", "WEBP", "JPEG"],),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
            },
            "optional": {
                "models": ("STRING", {"forceInput": True}),
                "extra_metadata": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def save(
        self,
        images,
        filename_prefix="ComfyUI",
        format="PNG",
        quality=95,
        models=None,
        extra_metadata=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        output_dir = folder_paths.get_output_directory()
        ext = format.lower()

        workflow_str = ""
        if extra_pnginfo and "workflow" in extra_pnginfo:
            workflow_str = json.dumps(extra_pnginfo["workflow"])

        prompt_str = json.dumps(prompt) if prompt else ""
        models_str = models if models else "[]"
        extra_str = extra_metadata if extra_metadata else "{}"

        results = []
        for i, tensor in enumerate(images):
            pil = _tensor_to_pil(tensor)
            xmp_str = _build_xmp(workflow_str, prompt_str, models_str, extra_str)
            xmp_bytes = xmp_str.encode("utf-8")
            path = _next_filename(output_dir, filename_prefix, ext)

            if format == "PNG":
                _save_png(pil, path, xmp_str, workflow_str, prompt_str)
            elif format == "WEBP":
                _save_webp(pil, path, xmp_bytes, quality)
            elif format == "JPEG":
                _save_jpeg(pil, path, xmp_bytes, quality)

            filename = os.path.basename(path)
            results.append({"filename": filename, "subfolder": "", "type": "output"})

        return {"ui": {"images": results}}
