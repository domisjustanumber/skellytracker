"""Print Markdown tables from results/results.jsonl. Usage: python -I -B summarize.py [ROWPREFIX ...]

The last line of each id wins (a re-run replaces an earlier line).
"""
import json
import sys
from pathlib import Path

JSONL = Path(__file__).resolve().parent.parent / "results" / "results.jsonl"


def f(v, nd=1):
    if v is None:
        return "-"
    if isinstance(v, float):
        if abs(v) < 0.01 and v != 0:
            return f"{v:.1e}"
        return f"{v:.{nd}f}"
    return str(v)


def cfg_text(j):
    parts = [f"{k}={v}" for k, v in j["provider_options"].items() if k not in ("nv_runtime_cache_path",)]
    parts += [f"[cfg]{k.replace('session.', '')}={v}" for k, v in j["session_config"].items()
              if k not in ("ep.context_file_path",)]
    parts += [f"[so]{k}={v}" for k, v in j["session_attrs"].items()]
    parts += [f"[env]{k}={v}" for k, v in j.get("env_vars", {}).items()]
    return "; ".join(parts) or "{}"


def row(d):
    j = d["job"]
    t = d.get("timing") or {}
    c = d.get("compare") or {}
    dec = d.get("decoded") or {}
    a = d.get("assignment") or {}
    cpu = a.get("CPUExecutionProvider")
    if j["row"] in ("REF",) or j["env"] == "cpu":
        cpu_txt = "all"
    else:
        cpu_txt = f"{cpu['nodes']} ({','.join(cpu['op_types'])})" if cpu else "0"
    if j["model_key"] == "rtmw":
        dtxt = f"{dec.get('flips_any', '-')}/{dec.get('flips_any_tophalf', '-')} | {f(dec.get('max_px_err'))}" if dec else "-"
    else:
        dtxt = f"{dec.get('det_ref', '-')}->{dec.get('det_cfg', '-')} | {f(dec.get('max_box_px'), 2)}" if dec else "-"
    note = []
    if not d.get("ok"):
        note.append("FAIL: " + (d.get("skipped") or d.get("error") or "")[:220].replace("|", "/").replace("\n", " "))
    if d.get("timeout"):
        note.append("TIMEOUT")
    if c.get("nan") or c.get("inf"):
        note.append(f"NaN {c.get('nan')} Inf {c.get('inf')}")
    if t:
        note.append(f"cpu {f(t.get('cpu_ms_per_run'))} ms/run")
    if d.get("repeat_identical") is False:
        note.append("repeat differs")
    if d.get("dir_after"):
        note.append(f"dir {d['dir_after']['files']} files {d['dir_after']['bytes'] // 1024} KB")
    if d.get("files"):
        note.append("files " + ", ".join(f"{k}={v}" for k, v in d["files"].items()))
    if "timing_run_only" in d:
        note.append(f"run-only {f(d['timing_run_only']['median_ms'], 2)} ms")
    if "second_run_ms" in d:
        note.append(f"2nd run {f(d['second_run_ms'])} ms")
    if "new_input_changed_output" in d:
        note.append(f"new input changes out: {d['new_input_changed_output']}, rel vs CPU {f(d.get('new_input_rel_vs_cpu'), 4)}, plain-run outs {d.get('plain_run_outputs')}")
    if d.get("plain_run_after_graph_error"):
        note.append("plain run err: " + d["plain_run_after_graph_error"][:120])
    if d.get("alloc_attempts"):
        okf = [x["form"] for x in d["alloc_attempts"] if x["ok"]]
        note.append(f"alloc forms ok: {sorted(set(okf))}")
    if d.get("multicam"):
        m = d["multicam"]
        note.append(f"fps {m['total_fps']} cpu {m['cpu_ms_per_frame']} ms/frame util {m['cpu_util']} med {m['median_ms']} p95 {m['p95_ms']}")
    if d.get("log_hits"):
        note.append("log: " + " // ".join(h.strip()[-160:] for h in d["log_hits"][:3]).replace("|", "/"))
    tag = j["id"].split("|", 4)[4] if j["id"].count("|") >= 4 else ""
    med = f"{f(t.get('median_ms'), 2)} ({f(t.get('p95_ms'), 2)})" if t else "-"
    rel = f"{f(c.get('max_abs'), 3)} / {f(c.get('max_rel'), 4)}" if "max_abs" in c else "-"
    return (f"| {j['row']} {tag} | {cfg_text(j)} | {j['model_key']} b{j['batch']}/{j['precision']} | "
            f"{f(d.get('build_ms'), 0)} | {med} | {rel} | {dtxt} | {cpu_txt} | {f(d.get('vram_peak_mb'), 0)} | "
            f"{'; '.join(note)} |")


def main():
    prefixes = sys.argv[1:]
    recs = {}
    for line in JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            recs[d["id"]] = d
    print("| row | options | model b/prec | build ms | median ms (p95) | max abs / rel | flips all/top or det ref->cfg | px err or box px | CPU nodes | VRAM MB | note |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for d in recs.values():
        if prefixes and not any(d["job"]["row"].startswith(p) for p in prefixes):
            continue
        print(row(d))


if __name__ == "__main__":
    main()
