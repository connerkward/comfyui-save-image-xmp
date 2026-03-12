import json
import os

import folder_paths

from .save_image_xmp import _build_xmp, _collect_model_hashes, _next_filename


class SaveLayeredTIFFXMP:
    INPUT_IS_LIST = True
    CATEGORY = "image"
    OUTPUT_NODE = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("filepath",)
    FUNCTION = "save"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preview_image": ("IMAGE",),
                "preview_name": ("STRING", {"default": "preview"}),
                "filename_prefix": ("STRING", {"default": "ComfyUI-XMP"}),
                "author": ("STRING", {"default": ""}),
                "sidecar_xmp": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "layers": ("IMAGE",),
                "layer_names": ("STRING", {"forceInput": True}),
                "json_metadata": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def save(
        self,
        preview_image,    # list[IMAGE tensor]
        preview_name,     # list[str]
        filename_prefix,  # list[str]
        author=None,      # list[str]
        sidecar_xmp=None, # list[bool]
        layers=None,      # list[IMAGE tensor] — one entry per connected image
        layer_names=None, # list[str] — optional names aligned to layers
        json_metadata=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        import tifffile
        from PIL import Image

        pv_name = preview_name[0] if preview_name else "preview"
        prefix = filename_prefix[0] if filename_prefix else "ComfyUI-XMP"
        author_str = author[0] if author else ""

        prompt_dict = prompt[0] if prompt else None
        workflow_str = ""
        if extra_pnginfo and extra_pnginfo[0] and "workflow" in extra_pnginfo[0]:
            workflow_str = json.dumps(extra_pnginfo[0]["workflow"])
        prompt_str = json.dumps(prompt_dict) if prompt_dict else ""
        models_str = _collect_model_hashes(prompt_dict)
        json_str = json_metadata[0] if json_metadata else "{}"

        # Page 0: preview
        preview_arr = (preview_image[0][0].cpu().numpy() * 255).clip(0, 255).astype("uint8")
        all_layers = [(pv_name, preview_arr)]

        # Additional layers from any IMAGE connections
        if layers:
            for i, layer_tensor in enumerate(layers):
                name = layer_names[i] if layer_names and i < len(layer_names) else f"layer-{i+1:02d}"
                arr = (layer_tensor[0].cpu().numpy() * 255).clip(0, 255).astype("uint8")
                all_layers.append((name, arr))

        layers_str = ",".join(name for name, _ in all_layers)
        xmp_bytes = _build_xmp(workflow_str, prompt_str, models_str, json_str, layers_str, author_str).encode("utf-8")

        output_dir = folder_paths.get_output_directory()
        tiff_path = _next_filename(output_dir, prefix, "tiff")

        with tifffile.TiffWriter(tiff_path, bigtiff=False) as tif:
            for i, (name, arr) in enumerate(all_layers):
                extratags = [(285, "s", 0, name, True)]
                if i == 0:
                    extratags.append((700, "B", 0, xmp_bytes, True))
                tif.write(
                    arr,
                    compression="deflate",
                    compressionargs={"level": 9},
                    predictor=2,
                    extratags=extratags,
                    metadata=None,
                )

        write_sidecar = sidecar_xmp[0] if sidecar_xmp else False
        if write_sidecar:
            xmp_path = os.path.splitext(tiff_path)[0] + ".xmp"
            with open(xmp_path, "wb") as f:
                f.write(xmp_bytes)

        temp_dir = folder_paths.get_temp_directory()
        base = os.path.splitext(os.path.basename(tiff_path))[0]
        ui_images = []
        for i, (name, arr) in enumerate(all_layers):
            fname = f"{base}_layer{i:02d}_{name}.png"
            Image.fromarray(arr).save(os.path.join(temp_dir, fname), format="PNG")
            ui_images.append({"filename": fname, "subfolder": "", "type": "temp"})

        return {
            "ui": {"images": ui_images},
            "result": (tiff_path,),
        }
