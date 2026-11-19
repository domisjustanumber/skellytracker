# Evidence of ADR-FBV5. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Compare the runs of measure.py. Writes analysis.json and prints the tables.

Points: the 133 model points of the 137-point output (the 4 derived centers, indices 23..26, are left out).
Threshold 0.4: the score_threshold of points_box and the min_score of the trigger in the built-in pipeline.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
THR = 0.4
W, H = 720, 1280
GROUPS = {"body": range(0, 17), "feet": range(17, 23), "face": range(27, 95), "left_hand": range(95, 116), "right_hand": range(116, 137)}
MODEL = np.array([i for g in GROUPS.values() for i in g])
NAMES = json.loads((HERE / "output_schema.json").read_text())["wholebody"]["point_names"]
BINS = [(0, 0), (1, 4), (5, 14), (15, 29), (30, 59), (60, 89), (90, 119), (120, 149), (150, 10**6)]


def load(tag, frames=None):
    z = dict(np.load(RUNS / f"{tag}.npz"))
    return {k: v[:frames] for k, v in z.items()} if frames else z


def st(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if not v.size:
        return {"n": 0}
    return {"n": int(v.size), "mean": float(v.mean()), "median": float(np.median(v)), "p95": float(np.percentile(v, 95)),
            "p99": float(np.percentile(v, 99)), "max": float(v.max())}


def since_det(det):
    """Frames since the last detector call, per (frame, camera), from the det flags of one run."""
    out = np.zeros(det.shape, int)
    last = np.full(det.shape[1], -10**6)
    for t in range(det.shape[0]):
        last = np.where(det[t], t, last)
        out[t] = t - last
    return out


def bitwise(a, b):
    keys = ["xy", "score", "kp_present", "box", "box_score", "box_present", "det"]
    return {k: bool(np.array_equal(a[k], b[k], equal_nan=True)) for k in keys}


def compare(ref_tag, oth_tag, frames=None):
    a, b = load(ref_tag, frames), load(oth_tag, frames)
    T = min(len(a["det"]), len(b["det"]))
    a, b = ({k: v[:T] for k, v in x.items()} for x in (a, b))
    res = {"ref": ref_tag, "other": oth_tag, "frames": T, "cams": int(a["det"].shape[1]), "bitwise_equal": bitwise(a, b)}
    # detections (delivered crop box = output `boxes`)
    res["people_count_mismatch_frames"] = int((a["box_present"] != b["box_present"]).any(axis=1).sum())
    res["people_count_mismatch_camframes"] = int((a["box_present"] != b["box_present"]).sum())
    res["kp_present_mismatch_camframes"] = int((a["kp_present"] != b["kp_present"]).sum())
    res["detector_ran_mismatch_frames"] = int((a["det"] != b["det"]).any(axis=1).sum())
    res["detector_calls"] = [int(a["det"].any(axis=1).sum()), int(b["det"].any(axis=1).sum())]
    res["box_present_fraction"] = [float(a["box_present"].mean()), float(b["box_present"].mean())]
    both = a["box_present"] & b["box_present"]
    corner = np.concatenate([np.hypot(*(a["box"][..., s] - b["box"][..., s]).transpose(2, 0, 1))[both] for s in (slice(0, 2), slice(2, 4))])
    res["box_corner_px"] = st(corner)
    res["box_corner_px_detector_frames"] = st(np.concatenate([np.hypot(*(a["box"][..., s] - b["box"][..., s]).transpose(2, 0, 1))[both & a["det"] & b["det"]]
                                                             for s in (slice(0, 2), slice(2, 4))]))
    res["box_score_abs"] = st(np.abs(a["box_score"] - b["box_score"])[both])
    # keypoints
    diag = np.hypot(a["box"][..., 2] - a["box"][..., 0], a["box"][..., 3] - a["box"][..., 1])  # ref crop box diagonal
    pres = a["kp_present"] & b["kp_present"]
    sa, sb = a["score"][:, :, MODEL], b["score"][:, :, MODEL]
    d = np.linalg.norm(a["xy"][:, :, MODEL] - b["xy"][:, :, MODEL], axis=-1)
    hi = pres[..., None] & (sa > THR) & (sb > THR)
    pct = d / diag[..., None] * 100.0
    res["kp_px"] = st(d[hi])
    res["kp_pct_diag"] = st(pct[hi])
    res["kp_score_abs_both_above"] = st(np.abs(sa - sb)[hi])
    res["kp_score_abs_all_present"] = st(np.abs(sa - sb)[pres[..., None].repeat(len(MODEL), -1)])
    pp = pres[..., None].repeat(len(MODEL), -1)
    flips = pp & ((sa > THR) != (sb > THR))
    res["above_thr_points"] = int(hi.sum())
    res["flips"] = int(flips.sum())
    res["flips_pct_of_present"] = float(100.0 * flips.sum() / max(pp.sum(), 1))
    res["flips_margin_abs_score_minus_thr"] = st(np.minimum(np.abs(sa - THR), np.abs(sb - THR))[flips])
    off = 0
    res["groups"] = {}
    for g, idx in GROUPS.items():
        sl = slice(off, off + len(idx))
        off += len(idx)
        res["groups"][g] = {"px": st(d[:, :, sl][hi[:, :, sl]]), "pct": st(pct[:, :, sl][hi[:, :, sl]]),
                            "flips": int(flips[:, :, sl].sum()), "above": int(hi[:, :, sl].sum())}
    # time since the last detector call (of the reference run)
    sd = since_det(a["det"])[..., None].repeat(len(MODEL), -1)
    res["since_detector"] = []
    for lo, hb in BINS:
        m = hi & (sd >= lo) & (sd <= hb)
        res["since_detector"].append({"bin": f"{lo}-{hb}" if hb < 10**6 else f"{lo}+", **{k: v for k, v in st(d[m]).items() if k in ("n", "mean", "median", "p95")}})
    # per-frame median difference over time (all cams pooled), to show drift or return to 0
    per_frame = [float(np.median(d[t][hi[t]])) if hi[t].any() else None for t in range(T)]
    res["per_frame_median_px_by_100"] = [float(np.median([x for x in per_frame[i:i + 100] if x is not None] or [np.nan])) for i in range(0, T, 100)]
    res["frames_all_points_equal"] = int(sum(1 for t in range(T) if hi[t].any() and np.all(d[t][hi[t]] == 0)))
    # worst 10
    idx = np.argwhere(hi)
    vals = d[hi]
    order = np.argsort(vals)[::-1][:10]
    worst = []
    for o in order:
        t, c, k = idx[o]
        x, y = a["xy"][t, c, MODEL[k]]
        worst.append({"cam": int(c), "frame": int(t), "point": NAMES[MODEL[k]], "score_ref": round(float(sa[t, c, k]), 3), "score_other": round(float(sb[t, c, k]), 3),
                      "px": round(float(vals[o]), 2), "pct_diag": round(float(pct[t, c, k]), 2), "since_det": int(sd[t, c, k]),
                      "border_px": round(float(min(x, y, W - x, H - y)), 1), "box_diag": round(float(diag[t, c]), 1),
                      "box_corner_diff": round(float(np.abs(a["box"][t, c] - b["box"][t, c]).max()), 2)})
    res["worst10"] = worst
    # worst 10 distinct events: (cam, frame, group) by the max point difference in the group
    res["pts_over_5pct"] = int((pct[hi] > 5).sum())
    res["pts_over_2pct"] = int((pct[hi] > 2).sum())
    events = []
    off = 0
    for g, gi in GROUPS.items():
        sl = slice(off, off + len(gi))
        off += len(gi)
        dg = np.where(hi[:, :, sl], d[:, :, sl], np.nan)
        with np.errstate(all="ignore"):
            mx = np.nanmax(dg, axis=-1)
        for t, c in np.argwhere(np.isfinite(mx)):
            events.append((float(mx[t, c]), g, int(t), int(c), sl))
    events.sort(key=lambda e: -e[0])
    ev_out = []
    for mx, g, t, c, sl in events[:10]:
        m = hi[t, c, sl]
        k = MODEL[sl][m]
        e = {"cam": c, "frame": t, "group": g, "max_px": round(mx, 1), "n_points": int(m.sum()), "mean_px": round(float(d[t, c, sl][m].mean()), 1),
             "score_ref_mean": round(float(sa[t, c, sl][m].mean()), 3), "score_other_mean": round(float(sb[t, c, sl][m].mean()), 3),
             "since_det": int(sd[t, c, 0]), "min_border_px": round(float(np.min([min(x, y, W - x, H - y) for x, y in a["xy"][t, c, k]])), 1),
             "box_diag": round(float(diag[t, c]), 1), "box_corner_diff": round(float(np.abs(a["box"][t, c] - b["box"][t, c]).max()), 2)}
        if g.endswith("hand"):  # is the other run's hand where the reference put the opposite hand?
            opp = GROUPS["right_hand" if g == "left_hand" else "left_hand"]
            e["other_centroid_to_ref_opposite_hand_px"] = round(float(np.linalg.norm(np.nanmean(b["xy"][t, c, k], 0) - np.nanmean(a["xy"][t, c, list(opp)], 0))), 1)
        ev_out.append(e)
    res["worst_events"] = ev_out
    return res


def short(r):
    k, p = r["kp_px"], r["kp_pct_diag"]
    if not k["n"]:
        return f"{r['ref']} vs {r['other']}: no common points"
    return (f"{r['ref']:>14} vs {r['other']:<14} T={r['frames']} cnt_mis={r['people_count_mismatch_camframes']} det_mis={r['detector_ran_mismatch_frames']} "
            f"box mean/p95/p99/max {r['box_corner_px'].get('mean', 0):.2f}/{r['box_corner_px'].get('p95', 0):.2f}/{r['box_corner_px'].get('p99', 0):.2f}/{r['box_corner_px'].get('max', 0):.2f} "
            f"kp px mean/med/p95/p99/max {k['mean']:.3f}/{k['median']:.3f}/{k['p95']:.3f}/{k['p99']:.2f}/{k['max']:.1f} "
            f"pct med/p99/max {p['median']:.3f}/{p['p99']:.2f}/{p['max']:.1f} flips {r['flips']} ({r['flips_pct_of_present']:.3f}%) n={k['n']}")


PAIRS = [("cuda_R", "cuda_R2"), ("cuda_R", "cuda_A1"), ("cuda_R", "cuda_J2"), ("cuda_R", "cuda_J3"), ("cuda_A1", "cuda_J2"),
         ("trt-rtx_R", "trt-rtx_R2"), ("trt-rtx_R", "trt-rtx_A1"), ("trt-rtx_R", "trt-rtx_J2"), ("trt-rtx_R", "trt-rtx_J3"), ("trt-rtx_A1", "trt-rtx_J2"),
         ("cuda_R", "cpu_R"), ("cuda_R", "trt-rtx_R"), ("cuda_R_q75", "cuda_J3_q75"), ("cuda_R@300", "cuda_J3@300"),
         ("cuda_R_i1", "cuda_J3_i1"), ("cuda_R_i1", "cpu_R_i1"), ("cuda_R_i1", "cuda_R2_i1")]


def main():
    out = []
    for ra, rb in PAIRS:
        frames = None
        if "@" in ra:
            ra, frames = ra.split("@")[0], int(ra.split("@")[1])
            rb = rb.split("@")[0]
        if not (RUNS / f"{ra}.npz").exists() or not (RUNS / f"{rb}.npz").exists():
            continue
        r = compare(ra, rb, frames)
        out.append(r)
        print(short(r), "bitwise" if all(r["bitwise_equal"].values()) else "")
    (HERE / "analysis.json").write_text(json.dumps(out, indent=1))
    if len(sys.argv) > 1:
        for r in out:
            if f"{r['ref']}|{r['other']}" in sys.argv[1:]:
                print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
