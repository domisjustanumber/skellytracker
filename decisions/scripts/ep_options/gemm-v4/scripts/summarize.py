"""Summarize results/results.jsonl into results/summary.json and print Markdown tables.

Usage: python -I -B summarize.py ROOT
"""
import hashlib
import json
import statistics
import sys
from pathlib import Path

import numpy as np

ROOT = Path(sys.argv[1])
RES = ROOT / "results"
rows = [json.loads(line) for line in (RES / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
by = {r["id"]: r for r in rows}
CFGS = [f"{s}_b{b}_{p}" for s in ("m", "x-384") for b in (1, 3) for p in ("fp32", "fp16")]
summary = {"passes": {}, "interleaved": {}, "determinism": {}, "probes": [], "tiny": []}


def parity(r):
    vb = r.get("vs_baseline") or {}
    if not vb:
        return {}
    return {"max_abs": max(v["max_abs"] for v in vb.values()),
            "max_rel_to_range": max(v["max_rel_to_range"] or 0 for v in vb.values()),
            "max_rel_elementwise": max(v["max_rel_elementwise"] for v in vb.values()),
            "per_output": {k: {"max_abs": v["max_abs"], "max_rel_elementwise": v["max_rel_elementwise"],
                               "bit_identical": v["bit_identical"]} for k, v in vb.items()},
            "bit_identical": all(v["bit_identical"] for v in vb.values()),
            **(r.get("decoded_vs_baseline") or {})}


def rec(r):
    t = r.get("timing") or {}
    return {"ok": r.get("ok"), "median_ms": t.get("median_ms"), "p95_ms": t.get("p95_ms"), "min_ms": t.get("min_ms"),
            "build_ms": r.get("build_ms"), "first_run_ms": r.get("first_run_ms"),
            "vram_peak_delta_mb": r.get("vram_peak_delta_mb"), "cpu_nodes": r.get("cpu_nodes"),
            "assignment": {k: v["nodes"] for k, v in (r.get("assignment") or {}).items()},
            "repeat_identical_after_timed": r.get("repeat_identical_after_timed"),
            "use_deterministic_compute_attr": r.get("use_deterministic_compute_attr"),
            "parity_vs_baseline": parity(r), "error": r.get("error")}


print("## Single passes\n")
for g in ("base", "gemm", "det", "base2"):
    summary["passes"][g] = {c: rec(by[f"{g}|{c}"]) for c in CFGS if f"{g}|{c}" in by}
    print(f"### {g}\n")
    print("| Config | median ms | p95 ms | min ms | first run ms | build ms | VRAM delta MB | CPU nodes | CUDA nodes | max abs vs base | flips | max px |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c, v in summary["passes"][g].items():
        p = v["parity_vs_baseline"]
        print(f"| {c} | {v['median_ms']} | {v['p95_ms']} | {v['min_ms']} | {v['first_run_ms']} | {v['build_ms']} | "
              f"{v['vram_peak_delta_mb']} | {v['cpu_nodes']} | {v['assignment'].get('CUDAExecutionProvider')} | "
              f"{p.get('max_abs', '(ref)')} | {p.get('argmax_flips', '-')} | {p.get('max_px_shift', '-')} |")
    print()

print("## Interleaved (3 rounds, rotated order; median of the 3 run medians, min of mins)\n")
print("| Config | base med | gemm med | det med | gemm vs base | det vs base | base min | gemm min | det min | all bit-identical |")
print("|---|---|---|---|---|---|---|---|---|---|")
for c in CFGS:
    arms = {}
    ident = True
    for a in ("base", "gemm", "det"):
        rr = [by[f"inter|{c}|{a}-r{i}"] for i in range(3)]
        meds = [x["timing"]["median_ms"] for x in rr]
        mins = [x["timing"]["min_ms"] for x in rr]
        p95s = [x["timing"]["p95_ms"] for x in rr]
        ident &= all(parity(x).get("bit_identical") for x in rr)
        arms[a] = {"run_medians": meds, "median_of_medians": statistics.median(meds), "min_of_mins": min(mins),
                   "p95s": p95s, "vram": [x.get("vram_peak_delta_mb") for x in rr],
                   "cpu_nodes": [x.get("cpu_nodes") for x in rr]}
    b = arms["base"]["median_of_medians"]
    for a in ("gemm", "det"):
        arms[a]["delta_pct_vs_base"] = round(100 * (arms[a]["median_of_medians"] - b) / b, 1)
    arms["all_bit_identical_to_baseline"] = ident
    summary["interleaved"][c] = arms
    print(f"| {c} | {b:.2f} | {arms['gemm']['median_of_medians']:.2f} | {arms['det']['median_of_medians']:.2f} | "
          f"{arms['gemm']['delta_pct_vs_base']:+.1f}% | {arms['det']['delta_pct_vs_base']:+.1f}% | "
          f"{arms['base']['min_of_mins']:.2f} | {arms['gemm']['min_of_mins']:.2f} | {arms['det']['min_of_mins']:.2f} | {ident} |")
print()

print("## Interleaved, m fp16, 8 rounds (inter r0-r2 plus inter2 r3-r7)\n")
print("| Config | arm | rounds | median of medians | min of mins | run medians |")
print("|---|---|---|---|---|---|")
summary["interleaved_m_fp16_8_rounds"] = {}
for c in ("m_b1_fp16", "m_b3_fp16"):
    for a in ("base", "gemm", "det"):
        rr = [by[f"inter|{c}|{a}-r{i}"] for i in range(3)] + [by[f"inter2|{c}|{a}-r{i}"] for i in range(3, 8)]
        meds = [x["timing"]["median_ms"] for x in rr]
        d = {"rounds": len(rr), "median_of_medians": statistics.median(meds),
             "min_of_mins": min(x["timing"]["min_ms"] for x in rr), "run_medians": meds,
             "all_bit_identical": all(parity(x).get("bit_identical") for x in rr)}
        summary["interleaved_m_fp16_8_rounds"][f"{c}|{a}"] = d
        print(f"| {c} | {a} | {d['rounds']} | {d['median_of_medians']:.2f} | {d['min_of_mins']:.2f} | {meds} |")
print()

print("## Determinism (fp32 b3, 10 fresh processes per mode)\n")
print("| Size | Mode | sessions | unique output hashes | max abs vs session 0 | identical to baseline | det == nodet |")
print("|---|---|---|---|---|---|---|")
for s in ("m", "x-384"):
    ref = dict(np.load(RES / "refs" / f"{s}_b3_fp32.npz"))
    first = {}
    hashes = {}
    for mode in ("nodet", "det"):
        outs = [dict(np.load(RES / "detrep" / f"{s}_b3_fp32_{mode}_{i}.npz")) for i in range(10)]
        hs = []
        for o in outs:
            h = hashlib.sha256()
            for k in sorted(o):
                h.update(np.ascontiguousarray(o[k]).tobytes())
            hs.append(h.hexdigest())
        mx = max(float(np.abs(o[k].astype(np.float64) - outs[0][k]).max()) for o in outs for k in o)
        same_ref = all(np.array_equal(o[k], ref[k]) for o in outs for k in o)
        first[mode], hashes[mode] = outs[0], set(hs)
        summary["determinism"][f"{s}|{mode}"] = {"sessions": len(outs), "unique_hashes": len(set(hs)),
                                                 "max_abs_vs_session0": mx, "identical_to_baseline": same_ref,
                                                 "cpu_nodes": [by[f"detrep|{s}_b3_fp32|{mode}-s{i}"]["cpu_nodes"] for i in range(10)],
                                                 "attr": [by[f"detrep|{s}_b3_fp32|{mode}-s{i}"]["use_deterministic_compute_attr"] for i in range(10)]}
    cross = hashes["nodet"] == hashes["det"]
    for mode in ("nodet", "det"):
        d = summary["determinism"][f"{s}|{mode}"]
        d["det_equals_nodet"] = cross
        print(f"| {s} | {mode} | {d['sessions']} | {d['unique_hashes']} | {d['max_abs_vs_session0']} | {d['identical_to_baseline']} | {cross} |")
print()

print("## Probes\n")
for r in rows:
    if r["id"].startswith(("probe|", "tiny|")):
        item = {"id": r["id"], "ok": r.get("ok"), "provider_options": r["job"]["provider_options"],
                "session_config": r["job"]["session_config"], "env_vars": r["job"]["env_vars"],
                "deterministic": r["job"]["deterministic"],
                "config_entry_ep.cuda.enable_gemm_auto_tune": (r.get("config_entries_after_add") or {}).get("ep.cuda.enable_gemm_auto_tune"),
                "error": (r.get("error") or "").split(" : ")[-1][:200], "timing": r.get("timing"),
                "bit_identical_vs_baseline": parity(r).get("bit_identical")}
        summary["probes" if r["id"].startswith("probe") else "tiny"].append(item)
        print(f"- {item['id']}: ok={item['ok']} po={item['provider_options']} cfg={item['session_config']} env={item['env_vars']} "
              f"entry={item['config_entry_ep.cuda.enable_gemm_auto_tune']} ident={item['bit_identical_vs_baseline']} err={item['error']}")
(RES / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
