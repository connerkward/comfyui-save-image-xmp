from .nodes import SaveImageXMP, SaveLayeredTIFFXMP

NODE_CLASS_MAPPINGS = {
    "SaveImageXMP": SaveImageXMP,
    "SaveLayeredTIFFXMP": SaveLayeredTIFFXMP,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageXMP": "Save Image (XMP)",
    "SaveLayeredTIFFXMP": "Save Layered TIFF (XMP)",
}

WEB_DIRECTORY = "./web"
