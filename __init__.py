from .nodes import ModelHashCollector, SaveImageXMP

NODE_CLASS_MAPPINGS = {
    "SaveImageXMP": SaveImageXMP,
    "ModelHashCollector": ModelHashCollector,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageXMP": "Save Image (XMP)",
    "ModelHashCollector": "Model Hash Collector",
}

WEB_DIRECTORY = "./web"
