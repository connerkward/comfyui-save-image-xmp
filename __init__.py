from .nodes import SaveImageXMP, SaveLayeredTIFFXMP, LayerPack

NODE_CLASS_MAPPINGS = {
    "SaveImageXMP": SaveImageXMP,
    "SaveLayeredTIFFXMP": SaveLayeredTIFFXMP,
    "LayerPack": LayerPack,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageXMP": "Save Image (XMP)",
    "SaveLayeredTIFFXMP": "Save Layered TIFF (XMP)",
    "LayerPack": "Layer Pack",
}

WEB_DIRECTORY = "./web"
