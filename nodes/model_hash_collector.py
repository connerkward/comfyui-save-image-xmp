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


def _all_model_dirs() -> list[str]:
    """All base dirs: registered folder_paths + direct subdirs of models_dir."""
    dirs: set[str] = set()
    for folder_type, (bases, _) in folder_paths.folder_names_and_paths.items():
        dirs.update(bases)
    # Also walk models_dir one level deep (catches unregistered: sam2, grounding-dino, etc.)
    models_dir = folder_paths.models_dir
    if os.path.isdir(models_dir):
        for name in os.listdir(models_dir):
            d = os.path.join(models_dir, name)
            if os.path.isdir(d):
                dirs.add(d)
    return list(dirs)


def _resolve(value: str) -> str | None:
    """
    1. Exact match via folder_paths across all registered subfolders.
    2. Stem match: scan all model dirs (registered + models_dir subdirs) for
       any file whose stem equals value (handles extensionless widget names).
    """
    # Pass 1: exact match through registered folder types
    for folder_type in folder_paths.folder_names_and_paths:
        path = folder_paths.get_full_path(folder_type, value)
        if path and os.path.isfile(path):
            return path

    # Pass 2: stem match (exact, then normalized) across all model dirs
    # Normalized: strip trailing parenthetical e.g. " (694MB)", lowercase
    import re
    normalized = re.sub(r'\s*\([^)]*\)\s*$', '', value).lower()

    for base in _all_model_dirs():
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
