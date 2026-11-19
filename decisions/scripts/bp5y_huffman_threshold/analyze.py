# Evidence of ADR-BP5Y. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Tables of runs/*.json (off vs on), the output comparison of the .npz files, and the log lines seen only with the option on."""
import json
import re
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R = HERE / "runs"
L = HERE / "logs"
CFGS = ["trt-rtx_720x3", "trt-rtx_720x6", "cuda_720x3", "cuda_720x6", "trt-rtx_1080x3", "cuda_1080x3"]


def f(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def s3(st):
    return f"{f(st['median'])} / {f(st['p95'])} / {f(st['max'])}"


out = ["## Pipeline yolox-rtmw-wholebody, M3 (JPEG, GPU decode, GPU preprocess), P1 cadence, 30 warm-up + 300 measured calls",
       "Values: median / p95 / max (ms). CPU: process_time per call, one value per block of 25 calls (12 blocks); mean in brackets.",
       "VRAM: process VRAM from LiveSampler (NVML), max of the samples before start, after start, at the first measured call, at the end.", "",
       "| config | run | frame.decode | wall per call | CPU per call | VRAM peak MiB | det calls | warnings | option seen |", "|---|---|---|---|---|---|---|---|---|"]
summary = ["", "## Mean of the 2 repeats (medians), on minus off", "", "| config | decode off | decode on | delta | wall off | wall on | delta | CPU mean off | CPU mean on | delta | VRAM off | VRAM on |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
equal = ["", "## Pipeline outputs, on vs off (same repeat, same frame sequence)", "", "| config | run | keypoint xy max abs diff | score max abs diff | box max abs diff | present differs | detector-ran differs |", "|---|---|---|---|---|---|---|"]
for cfg in CFGS:
    agg = {}
    for r in (1, 2):
        runs = {}
        for h in ("off", "on"):
            p = R / f"{cfg}_{h}_r{r}.json"
            if not p.exists():
                out.append(f"| {cfg} | {h} r{r} | missing | | | | | | |")
                continue
            s = json.loads(p.read_text())
            runs[h] = s
            sp = s["spans_all"]
            cpu = s["cpu_ms_per_call_blocks"]
            out.append(f"| {cfg} | {h} r{r} | {s3(sp['frame.decode'])} | {s3(s['wall'])} | {s3(cpu)} ({f(s['cpu_ms_per_call'])}) | "
                       f"{s['vram_peak_bytes'] / 2**20:.0f} | {s['detector_calls']} | {[w['code'] for w in s['warnings']] or 'none'} | {bool(s['huff_options_seen'])} |")
            a = agg.setdefault(h, {"dec": [], "wall": [], "cpu": [], "vram": []})
            a["dec"].append(sp["frame.decode"]["median"])
            a["wall"].append(s["wall"]["median"])
            a["cpu"].append(s["cpu_ms_per_call"])
            a["vram"].append(s["vram_peak_bytes"] / 2**20)
        if len(runs) == 2:
            x, y = (np.load(R / f"{cfg}_{h}_r{r}.npz") for h in ("off", "on"))
            both = x["kp_present"] & y["kp_present"]
            bb = x["box_present"] & y["box_present"]
            equal.append(f"| {cfg} | r{r} | {f(float(np.nanmax(np.abs(x['xy'][both] - y['xy'][both]))) if both.any() else None, 4)} | "
                         f"{f(float(np.abs(x['score'][both] - y['score'][both]).max()) if both.any() else None, 5)} | "
                         f"{f(float(np.nanmax(np.abs(x['box'][bb] - y['box'][bb]))) if bb.any() else None, 4)} | "
                         f"{int((x['kp_present'] != y['kp_present']).sum())} | {int((x['det'] != y['det']).sum())} |")
    if len(agg) == 2:
        m = {h: {k: float(np.mean(v)) for k, v in agg[h].items()} for h in agg}
        summary.append(f"| {cfg} | {f(m['off']['dec'])} | {f(m['on']['dec'])} | {m['on']['dec'] - m['off']['dec']:+.2f} | {f(m['off']['wall'])} | {f(m['on']['wall'])} | "
                       f"{m['on']['wall'] - m['off']['wall']:+.2f} | {f(m['off']['cpu'])} | {f(m['on']['cpu'])} | {m['on']['cpu'] - m['off']['cpu']:+.2f} | "
                       f"{m['off']['vram']:.0f} | {m['on']['vram']:.0f} |")

dec = ["", "## NvJpegDecoder alone (cuda EP device, 200 batches per block, 5 measured rounds + 1 warm-up, order rotated)", "",
       "Wall per batch median / p95 / max (ms); CPU per batch = process_time of a block / 200, median / p95 / max over the 5 blocks.", "",
       "| run | size | N | huff | wall | CPU |", "|---|---|---|---|---|---|"]
pix = ["", "## Pixels, option on vs off (decoder alone)", ""]
for p in sorted(R.glob("dec_*.json")):
    d = json.loads(p.read_text())
    for row in d["rows"]:
        dec.append(f"| {p.stem} | {row['size']} | {row['n']} | {row['huff']} | {f(row['wall_median'], 3)} / {f(row['wall_p95'], 3)} / {f(row['wall_max'], 3)} | "  # noqa: PERF401
                   f"{f(row['cpu_median'], 3)} / {f(row['cpu_p95'], 3)} / {f(row['cpu_max'], 3)} |")
    for name, v in d["pixels"].items():
        pix.append(f"- {p.stem} {name}: n {v['n']}, max abs diff {v['max_abs_diff_off_vs_on']}, None (off,on) {set(map(tuple, v['none_off_on']))}, off vs cv2 mean abs max {max(v['off_vs_cv2_mean_abs'])}")

# log lines (normalised) that appear only in "on" logs or only in "off" logs
NOISE = re.compile(r"^(gpu before|.*: start \d|skellytracker from|PIXELS|ROW|pixels |open |options of|DONE|\d+x\d+: mean)")


def lines(tag_glob):
    seen = {}
    for p in L.glob(tag_glob):
        for ln in p.read_text(errors="replace").splitlines():
            if NOISE.match(ln):
                continue
            key = re.sub(r"\d+(\.\d+)?", "#", ln.strip())[:200]
            seen[key] = seen.get(key, 0) + 1
    return seen


off_l, on_l = lines("*_off_r*.log"), lines("*_on_r*.log")
logs = ["", "## Log lines only with the option on (pipeline runs; digits normalised)", ""]
logs += [f"- ({n}x) {k}" for k, n in on_l.items() if k not in off_l] or ["- none"]
logs += ["", "## Log lines only with the option off", ""] + ([f"- ({n}x) {k}" for k, n in off_l.items() if k not in on_l] or ["- none"])
logs += ["", "## Log lines in both (count off / on)", ""] + [f"- ({off_l[k]} / {on_l[k]}) {k}" for k in on_l if k in off_l]
drv = (L / "driver_plan_main.log").read_text() if (L / "driver_plan_main.log").exists() else ""
text = "\n".join(out + summary + equal + dec + pix + logs + ["", "## Driver log", "", "```", drv, "```"])
(HERE / "tables.md").write_text(text)
print(text)
