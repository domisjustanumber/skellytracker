# Evidence of ADR-1SZ9. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Tables from runs/*.json and the results equality from runs/*.npz. Writes results.md and prints it."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
THRESH = 0.4
runs = {p.stem: json.loads(p.read_text()) for p in sorted(RUNS.glob("*.json"))}
out = []


def p(line=""):
    out.append(line)


def f(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def mib(b):
    return "-" if b is None else f"{b / 2**20:.0f}"


# Main tables
for prefix, title in (("A", "P1: built-in cadence (detector 1 in 150, keypoints each call), config variant for frames with no person"),
                      ("B", "P0: built-in config unchanged (frames hold no person: detector each call, keypoint model never)"),
                      ("D", "P1d: P1 with redetect_interval 1 (detector + keypoints each call)")):
    p(f"## {title}")
    p("| tag | wall med (p95, max) ms | calls/s | CPU ms/call (blocks min-max) | det calls | VRAM proc start->end MiB | start s | first call ms | warnings |")
    p("|---|---|---|---|---|---|---|---|---|")
    for tag, s in runs.items():
        if not tag.startswith(prefix + "_"):
            continue
        w, c, m = s["wall"], s["cpu_ms_per_call_blocks"], s["memory"]
        p(f"| {tag[2:]} | {f(w['median'])} ({f(w['p95'])}, {f(w['max'])}) | {f(s['calls_per_s'], 1)} | {f(s['cpu_ms_per_call'], 1)} ({f(c and c['min'], 1)}-{f(c and c['max'], 1)}) | "
          f"{s['detector_calls']} | {mib(m['start_measured']['process_vram_bytes'])}->{mib(m['end_measured']['process_vram_bytes'])} | {f(s['start_s'], 1)} | {f(s['first_call_ms'], 1)} | "
          f"{','.join(sorted({x['code'] for x in s['warnings']})) or 'none'} |")
    p()

KEYS = ["frame.decode", "frame.upload", "person.preprocess", "person.inference", "person.postprocess",
        "wholebody.preprocess", "wholebody.inference", "wholebody.postprocess", "glue.run", "pipeline.run", "wall"]
p("## Spans, median ms per call (p95 in brackets for pipeline.run)")
p("| tag | call type | n | " + " | ".join(k.replace("wholebody", "wb").replace("person", "det") for k in KEYS) + " |")
p("|---|---|---|" + "---|" * len(KEYS))
for tag, s in runs.items():
    if not (tag.startswith(("A_", "D_", "B_", "X_"))):
        continue
    for kind in ("spans_detector", "spans_keypoint_only"):
        t = s[kind]
        if not t or not t["wall"]:
            continue
        cells = []
        for k in KEYS:
            v = t[k]
            cells.append("-" if v is None else (f"{v['median']:.2f} ({v['p95']:.2f})" if k == "pipeline.run" else f"{v['median']:.2f}"))
        p(f"| {tag} | {kind[6:]} | {t['wall']['n']} | " + " | ".join(cells) + " |")
p()


def load(tag):
    path = RUNS / f"{tag}.npz"
    return np.load(path) if path.exists() else None


def compare(a, b):
    both = a["kp_present"] & b["kp_present"]
    conf = both[..., None] & (a["score"] > THRESH) & (b["score"] > THRESH)
    d = np.abs(a["xy"] - b["xy"])  # (calls, cams, C, 2)
    dk = d[conf]
    dall = d[both]
    bb = a["box_present"] & b["box_present"]
    db = np.abs(a["box"] - b["box"])[bb]
    ds = np.abs(a["box_score"] - b["box_score"])[bb]
    sk = np.abs(a["score"] - b["score"])[both]
    return {
        "calls": int(a["kp_present"].shape[0]), "kp_conf_n": int(conf.sum()), "kp_conf_max": float(dk.max()) if dk.size else None,
        "kp_conf_mean": float(dk.mean()) if dk.size else None, "kp_all_max": float(dall.max()) if dall.size else None,
        "kp_all_mean": float(dall.mean()) if dall.size else None, "kp_all_p99": float(np.percentile(dall, 99)) if dall.size else None,
        "kp_score_max": float(sk.max()) if sk.size else None,
        "box_max": float(db.max()) if db.size else None, "box_mean": float(db.mean()) if db.size else None,
        "box_score_max": float(ds.max()) if ds.size else None,
        "count_differs": int((a["box_present"] != b["box_present"]).sum()), "det_differs": int((a["det"] != b["det"]).sum()),
        "kp_present_differs": int((a["kp_present"] != b["kp_present"]).sum()),
        "conf_set_differs": int(((a["score"] > THRESH) != (b["score"] > THRESH))[both].sum()),
    }


p(f"## Results equality vs M0 (same frame sequence; keypoint threshold {THRESH}; differences in source pixels)")
p("| config | pair | calls x cams | kp>0.4 n | kp>0.4 max / mean | all kp max / p99 / mean | kp score max | box corner max / mean | box score max | count differs | detector-ran differs | kp>0.4 set differs |")
p("|---|---|---|---|---|---|---|---|---|---|---|---|")
for prefix in ("A", "D", "B"):
    for ep in ("cuda", "trt-rtx"):
        for cfg in ("720x3", "720x6", "1080x3", "1080x6"):
            base = load(f"{prefix}_{ep}_M0_{cfg}")
            if base is None:
                continue
            for m in ("M1", "M2", "M3"):
                other = load(f"{prefix}_{ep}_{m}_{cfg}")
                if other is None:
                    continue
                r = compare(base, other)
                p(f"| {prefix} {ep} {cfg} | {m} vs M0 | {r['calls']}x{base['det'].shape[1]} | {r['kp_conf_n']} | {f(r['kp_conf_max'], 3)} / {f(r['kp_conf_mean'], 4)} | "
                  f"{f(r['kp_all_max'], 2)} / {f(r['kp_all_p99'], 3)} / {f(r['kp_all_mean'], 4)} | {f(r['kp_score_max'], 4)} | {f(r['box_max'], 3)} / {f(r['box_mean'], 4)} | "
                  f"{f(r['box_score_max'], 5)} | {r['count_differs']} | {r['det_differs']} | {r['conf_set_differs']} |")
p()

p("## Other facts")
for tag, s in runs.items():
    if tag.startswith(("cold", "prefill", "X_")) or tag in ("A_cuda_M3_720x3", "A_trt-rtx_M3_720x3"):
        p(f"- {tag}: start {f(s['start_s'], 2)} s, first calls ms {[round(x, 1) for x in s['first_calls_ms']]}, first-call spans "
          f"{ {k: round(v, 1) for k, v in s['first_call_spans'].items() if v} }, wall med {f(s['wall']['median'])}, huff {s['huff_options_seen'][:1]}, "
          f"warnings {[(x['code'], x['details']) for x in s['warnings']]}, preprocess sessions {s['preprocess_sessions']}")
any_run = next(iter(runs.values()))
p(f"- execution facts (one run): {json.dumps({k: {kk: v[kk] for kk in ('used_ep', 'ep_options', 'cpu_nodes', 'cpu_op_types')} for k, v in any_run['execution'].items()})}")
for tag in ("A_cuda_M3_720x3", "A_trt-rtx_M3_720x3", "A_cuda_M3_720x6", "A_trt-rtx_M3_1080x6"):
    if tag in runs:
        p(f"- {tag} batching {runs[tag]['batching']}, memory {json.dumps({k: (mib(v['process_vram_bytes']), mib(v['gpu_used_bytes'])) for k, v in runs[tag]['memory'].items()})}")
text = "\n".join(out)
(HERE / "results.md").write_text(text, encoding="utf-8")
print(text)
