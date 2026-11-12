"""Check the v4 hash, opset and I/O of the models used. Usage: python -I -B check_models.py MANIFEST EXPDIR OUT"""
import hashlib
import json
import re
import sys
from pathlib import Path
import onnx

man = Path(sys.argv[1]).read_text(encoding="utf-8")
exp = Path(sys.argv[2])
pairs = re.findall(r'"path":\s*"[^"]*/(rtmw-wholebody133-[^"/]+\.onnx)"[\s\S]*?"sha256":\s*"([0-9a-f]{64})"', man)
want = dict(pairs)
out = {}
for size in ("m", "x-384"):
    for b in (1, 3):
        for p in ("fp32", "fp16"):
            name = f"rtmw-wholebody133-{size}_b{b}_{p}.onnx"
            f = exp / name
            h = hashlib.sha256(f.read_bytes()).hexdigest()
            m = onnx.load(str(f), load_external_data=False)
            out[name] = {"sha256": h, "v4_manifest_sha256": want.get(name), "matches_v4": h == want.get(name),
                         "opset_import": {(o.domain or "ai.onnx"): o.version for o in m.opset_import},
                         "ir_version": m.ir_version, "producer": f"{m.producer_name} {m.producer_version}",
                         "inputs": [(i.name, [d.dim_value or d.dim_param for d in i.type.tensor_type.shape.dim], i.type.tensor_type.elem_type) for i in m.graph.input],
                         "outputs": [(o.name, [d.dim_value or d.dim_param for d in o.type.tensor_type.shape.dim], o.type.tensor_type.elem_type) for o in m.graph.output],
                         "nodes": len(m.graph.node)}
            print(name, out[name]["matches_v4"], out[name]["opset_import"], out[name]["inputs"], out[name]["outputs"])
Path(sys.argv[3]).write_text(json.dumps(out, indent=1), encoding="utf-8")
