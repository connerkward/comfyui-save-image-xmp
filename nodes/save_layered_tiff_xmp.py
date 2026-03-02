import json
import os

import folder_paths

from .save_image_xmp import _build_xmp, _next_filename, _tensor_to_pil


class SaveLayeredTIFFXMP:
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
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
            },
            "optional": {
                "layers": ("LAYERS",),
                "model_hashes": ("STRING", {"forceInput": True}),
                "json_metadata": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def save(
        self,
        preview_image,
        preview_name="preview",
        filename_prefix="ComfyUI",
        layers=None,
        model_hashes=None,
        json_metadata=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        import tifffile

        workflow_str = ""
        if extra_pnginfo and "workflow" in extra_pnginfo:
            workflow_str = json.dumps(extra_pnginfo["workflow"])
        prompt_str = json.dumps(prompt) if prompt else ""
        models_str = model_hashes if model_hashes else "[]"
        extra_str = json_metadata if json_metadata else "{}"

        preview_arr = (preview_image[0].cpu().numpy() * 255).clip(0, 255).astype("uint8")
        all_layers = [(preview_name, preview_arr)] + (layers or [])

        layers_str = ",".join(name for name, _ in all_layers)
        xmp_bytes = _build_xmp(workflow_str, prompt_str, models_str, extra_str, layers_str).encode("utf-8")

        output_dir = folder_paths.get_output_directory()
        tiff_path = _next_filename(output_dir, filename_prefix, "tiff")

        with tifffile.TiffWriter(tiff_path, bigtiff=False) as tif:
            for i, (name, arr) in enumerate(all_layers):
                extratags = [(285, "s", 0, name, True)]  # PageName
                if i == 0:
                    extratags.append((700, "B", 0, xmp_bytes, True))  # XMP
                tif.write(
                    arr,
                    compression="deflate",
                    compressionargs={"level": 6},
                    extratags=extratags,
                    metadata=None,
                )

        pil = _tensor_to_pil(preview_image[0])
        temp_dir = folder_paths.get_temp_directory()
        preview_filename = os.path.splitext(os.path.basename(tiff_path))[0] + "_preview.png"
        pil.save(os.path.join(temp_dir, preview_filename), format="PNG")

        return {
            "ui": {"images": [{"filename": preview_filename, "subfolder": "", "type": "temp"}]},
            "result": (tiff_path,),
        }
