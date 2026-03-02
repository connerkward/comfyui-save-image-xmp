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


def _resolve(value: str) -> str | None:
    """
    1. Exact match via folder_paths across all registered subfolders.
    2. Prefix match: scan each base dir for any file whose stem starts with value.
    """
    for folder_type, (dirs, _) in folder_paths.folder_names_and_paths.items():
        # Exact match (handles filenames with known extensions)
        path = folder_paths.get_full_path(folder_type, value)
        if path and os.path.isfile(path):
            return path
        # Prefix match (handles widget values without extension, e.g. SAM2, GroundingDINO)
        for base in dirs:
            if not os.path.isdir(base):
                continue
            for fname in os.listdir(base):
                stem = os.path.splitext(fname)[0]
                if stem == value or fname == value:
                    full = os.path.join(base, fname)
                    if os.path.isfile(full):
                        return full
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
                # Skip obvious non-filenames
                if len(value) > 260 or value.startswith("http"):
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
