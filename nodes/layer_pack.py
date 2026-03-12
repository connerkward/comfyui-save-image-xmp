class LayerPack:
    CATEGORY = "image"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("layers", "layer_names")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "pack"

    MAX_LAYERS = 16

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(1, cls.MAX_LAYERS + 1):
            optional[f"image_{i}"] = ("IMAGE",)
            optional[f"name_{i}"] = ("STRING", {"default": f"layer-{i}"})
        return {"optional": optional}

    def pack(self, **kwargs):
        images, names = [], []
        for i in range(1, self.MAX_LAYERS + 1):
            img = kwargs.get(f"image_{i}")
            if img is not None:
                images.append(img)
                names.append(kwargs.get(f"name_{i}", f"layer-{i}"))
        return (images, names)
