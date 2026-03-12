class LayerPack:
    CATEGORY = "image"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("layers", "layer_names")
    OUTPUT_IS_LIST = (True, True)
    FUNCTION = "pack"

    _LAYERS = [
        ("lama_smudge",   "lama-smudge"),
        ("pad_mask",      "pad-mask"),
        ("outpaint_blur", "outpaint-blur"),
        ("outpaint_ui",   "outpaint-ui"),
        ("verify_hm_1",   "verify-hm-1"),
        ("verify_hm_2",   "verify-hm-2"),
        ("verify_hm_3",   "verify-hm-3"),
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {key: ("IMAGE",) for key, _ in cls._LAYERS},
        }

    def pack(self, **kwargs):
        images, names = [], []
        for key, display in self._LAYERS:
            if kwargs.get(key) is not None:
                images.append(kwargs[key])
                names.append(display)
        return (images, names)
