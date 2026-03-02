from .nodes import ModelHashCollector, SaveImageXMP, SaveLayeredTIFFXMP

NODE_CLASS_MAPPINGS = {
    "SaveImageXMP": SaveImageXMP,
    "ModelHashCollector": ModelHashCollector,
    "SaveLayeredTIFFXMP": SaveLayeredTIFFXMP,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageXMP": "Save Image (XMP)",
    "ModelHashCollector": "Model Hash Collector",
    "SaveLayeredTIFFXMP": "Save Layered TIFF (XMP)",
}

WEB_DIRECTORY = "./web"
