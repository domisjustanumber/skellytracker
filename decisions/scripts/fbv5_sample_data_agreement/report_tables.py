# Evidence of ADR-FBV5. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
import json, sys  # noqa: E401
R = json.load(open(sys.argv[1] + "/analysis.json"))
f = lambda s, k: f"{s.get(k, float('nan')):.2f}" if s.get("n") else "-"  # noqa: E731
print("pair | T | cnt_mis | det_mis | box mean/p95/p99/max | box det-frames max | box score max | kp px mean/med/p95/p99/max | %diag med/p95/p99/max | flips (pct) | pts>2% | pts>5% | score abs med/p99")
for r in R:
    b, k, p = r["box_corner_px"], r["kp_px"], r["kp_pct_diag"]
    print(f"{r['ref']} vs {r['other']} | {r['frames']} | {r['people_count_mismatch_camframes']} | {r['detector_ran_mismatch_frames']} | "
          f"{f(b,'mean')}/{f(b,'p95')}/{f(b,'p99')}/{f(b,'max')} | {f(r['box_corner_px_detector_frames'],'max')} | {f(r['box_score_abs'],'max')} | "
          f"{f(k,'mean')}/{f(k,'median')}/{f(k,'p95')}/{f(k,'p99')}/{f(k,'max')} | {f(p,'median')}/{f(p,'p95')}/{f(p,'p99')}/{f(p,'max')} | "
          f"{r['flips']} ({r['flips_pct_of_present']:.3f}) | {r.get('pts_over_2pct')} | {r.get('pts_over_5pct')} | {f(r['kp_score_abs_both_above'],'median')}/{f(r['kp_score_abs_both_above'],'p99')}")
sel = {("cuda_R","cuda_J3",1108), ("trt-rtx_R","trt-rtx_J3",1108), ("cuda_R","cpu_R",1108), ("cuda_R","trt-rtx_R",1108), ("cuda_R_i1","cuda_J3_i1",1108), ("cuda_R_i1","cpu_R_i1",1108)}
for r in R:
    if (r["ref"], r["other"], r["frames"]) not in sel: continue  # noqa: E701
    print("\n##", r["ref"], "vs", r["other"])
    print("groups:", {g: (f(v["px"],"median"), f(v["px"],"p99"), f(v["px"],"max"), f(v["pct"],"p99"), v["flips"], v["above"]) for g, v in r["groups"].items()})
    print("since_det:", [(x["bin"], x["n"], round(x.get("mean", 0), 2), round(x.get("median", 0), 2)) for x in r["since_detector"]])
    print("per100 median:", [round(x, 2) for x in r["per_frame_median_px_by_100"]])
    print("flip margin:", {k: round(v, 3) for k, v in r["flips_margin_abs_score_minus_thr"].items()})
    for e in r["worst_events"]: print("  ", e)  # noqa: E701
