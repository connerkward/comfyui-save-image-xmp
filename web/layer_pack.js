import { app } from "../../scripts/app.js";

const MAX = 16;

function toggleWidget(widget, show) {
    if (show) {
        widget.type = widget._origType || "text";
        delete widget.computeSize;
    } else {
        widget._origType = widget._origType || widget.type;
        widget.type = "converted-widget";
        widget.computeSize = () => [0, -4];
    }
}

function applySlotCount(node, count) {
    count = Math.max(1, Math.min(MAX, count));
    node.properties.slot_count = count;

    // Remove image inputs beyond count (iterate backward for safe removal)
    for (let i = node.inputs.length - 1; i >= 0; i--) {
        const m = node.inputs[i].name.match(/^image_(\d+)$/);
        if (m && parseInt(m[1]) > count) {
            node.removeInput(i);
        }
    }

    // Add missing image inputs up to count
    const existing = new Set(node.inputs.map((inp) => inp.name));
    for (let i = 1; i <= count; i++) {
        const name = `image_${i}`;
        if (!existing.has(name)) {
            node.addInput(name, "IMAGE");
        }
    }

    // Show/hide name widgets
    for (const w of node.widgets || []) {
        const m = w.name.match(/^name_(\d+)$/);
        if (m) {
            toggleWidget(w, parseInt(m[1]) <= count);
        }
    }

    node.setSize(node.computeSize());
    app.graph?.setDirtyCanvas(true);
}

app.registerExtension({
    name: "comfyui-save-image-xmp.LayerPack",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "LayerPack") return;

        const onCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onCreated?.apply(this, arguments);

            if (!this.properties) this.properties = {};
            if (!this.properties.slot_count) this.properties.slot_count = 1;

            this.addWidget("button", "Add Layer", null, () => {
                const c = this.properties.slot_count || 1;
                if (c < MAX) applySlotCount(this, c + 1);
            });

            this.addWidget("button", "Remove Layer", null, () => {
                const c = this.properties.slot_count || 1;
                if (c > 1) applySlotCount(this, c - 1);
            });

            // Defer so ComfyUI finishes adding all inputs/widgets first
            setTimeout(() => applySlotCount(this, this.properties.slot_count || 1), 0);
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (info) {
            onConfigure?.apply(this, arguments);
            const count = info?.properties?.slot_count || 1;
            this.properties.slot_count = count;
            applySlotCount(this, count);
        };
    },
});
