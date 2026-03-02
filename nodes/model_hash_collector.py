import hashlib
import json
import os

import folder_paths

_hash_cache: dict[str, str] = {}


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


def _resolve(filename: str) -> str | None:
    """Try folder_paths across all registered subfolders, return first hit."""
    for folder_type in folder_paths.folder_names_and_paths:
        path = folder_paths.get_full_path(folder_type, filename)
        if path and os.path.isfile(path):
            return path
    return None


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
            inputs = node.get("inputs", {})
            for value in inputs.values():
                if not isinstance(value, str) or not value:
                    continue
                # Skip obvious non-filenames (long strings, no extension, URLs)
                if len(value) > 260 or "." not in value or value.startswith("http"):
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

        return (json.dumps(results),)
