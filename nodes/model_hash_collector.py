import hashlib
import json

import folder_paths

_hash_cache: dict[str, str] = {}

_LOADER_FIELDS: dict[str, list[str]] = {
    "CheckpointLoaderSimple": ["ckpt_name"],
    "UNETLoader": ["unet_name"],
    "LoraLoader": ["lora_name"],
    "CLIPLoader": ["clip_name"],
    "VAELoader": ["vae_name"],
    "UnetLoaderGGUF": ["unet_name"],
}

_SUBFOLDER: dict[str, str] = {
    "ckpt_name": "checkpoints",
    "unet_name": "diffusion_models",
    "lora_name": "loras",
    "clip_name": "clip",
    "vae_name": "vae",
}


def _sha256(path: str) -> str:
    if path in _hash_cache:
        return _hash_cache[path]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    digest = h.hexdigest()
    _hash_cache[path] = digest
    return digest


class ModelHashCollector:
    CATEGORY = "image"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("models_json",)
    FUNCTION = "collect"

    @classmethod
    def INPUT_TYPES(cls):
        return {"hidden": {"prompt": "PROMPT"}}

    def collect(self, prompt=None):
        results = []
        seen: set[str] = set()

        if not prompt:
            return (json.dumps(results),)

        for node in prompt.values():
            class_type = node.get("class_type", "")
            fields = _LOADER_FIELDS.get(class_type, [])
            inputs = node.get("inputs", {})
            for field in fields:
                filename = inputs.get(field)
                if not filename or not isinstance(filename, str):
                    continue
                subfolder = _SUBFOLDER.get(field, "")
                full_path = folder_paths.get_full_path(subfolder, filename)
                if not full_path or full_path in seen:
                    continue
                seen.add(full_path)
                try:
                    digest = _sha256(full_path)
                except OSError:
                    digest = ""
                results.append({"name": filename, "path": full_path, "sha256": digest})

        return (json.dumps(results),)
