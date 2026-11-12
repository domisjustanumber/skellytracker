"""Test: does a VIDEO-mode MediaPipe landmarker stay empty after it loses tracking?"""
import json, sys, cv2, numpy as np, mediapipe as mp
from pathlib import Path
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (PoseLandmarker, PoseLandmarkerOptions,
    HandLandmarker, HandLandmarkerOptions, RunningMode)

M = Path.home() / ".freemocap" / "skellytracker-models"
POSE = M / "d9347aa2_pose_landmarker_heavy.task"   # repo default: HEAVY
HAND = M / "de73a113_hand_landmarker.task"
VID = Path.home() / ".cache/skellytracker/test_data/freemocap_test_data/synchronized_videos/sesh_2022-09-19_16_16_50_in_class_jsm_synced_Cam1.mp4"
OUT = Path(__file__).parent

cap = cv2.VideoCapture(str(VID))
frames = []
for _ in range(90):
    ok, f = cap.read(); assert ok
    frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
cap.release()
H, W = frames[0].shape[:2]

black = np.zeros_like(frames[0])
strip = frames[0][:, int(W * 0.80):]                     # right strip: no person in it
background = np.ascontiguousarray(np.tile(strip, (1, W // strip.shape[1] + 1, 1))[:, :W])
blur = cv2.GaussianBlur(frames[0], (0, 0), 40)
def shift(img, fx):  # translate right by fx*W, black fill
    return cv2.warpAffine(img, np.float32([[1, 0, fx * W], [0, 1, 0]]), (W, H))
def scale(img, s):   # shrink about the center
    return cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H / 2), 0, s), (W, H))

before, after = frames[:30], frames[:60]
SEQS = {  # name -> (before+gap frames, after frames)
    "1 black gap":      (before + [black] * 30, after),
    "2a background gap": (before + [background] * 30, after),
    "2b blur gap":      (before + [blur] * 30, after),
    "3a jump shift40%": (before, [shift(f, 0.40) for f in frames[30:90]]),
    "3b jump scale0.5": (before, [scale(f, 0.5) for f in frames[30:90]]),
}

def build(kind, mode, track):
    base = BaseOptions(model_asset_path=str(POSE if kind == "pose" else HAND))
    if kind == "pose":
        return PoseLandmarker.create_from_options(PoseLandmarkerOptions(base_options=base, running_mode=mode,
            num_poses=1, min_pose_detection_confidence=0.5, min_pose_presence_confidence=0.5, min_tracking_confidence=track))
    return HandLandmarker.create_from_options(HandLandmarkerOptions(base_options=base, running_mode=mode,
        num_hands=2, min_hand_detection_confidence=0.5, min_hand_presence_confidence=0.5, min_tracking_confidence=track))

def run(kind, mode, track, imgs):
    lm = build(kind, mode, track)
    out = []
    try:
        for i, a in enumerate(imgs):
            im = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a))
            r = lm.detect_for_video(im, i * 33) if mode == RunningMode.VIDEO else lm.detect(im)
            L = r.pose_landmarks if kind == "pose" else r.hand_landmarks
            cx = round(float(np.mean([p.x for p in L[0]])), 2) if L else None
            out.append((len(L), cx))
    finally:
        lm.close()
    return out

def first_found(res):
    return next((i for i, (n, _) in enumerate(res) if n), None)

def s(res): return "".join(str(min(n, 9)) if n else "." for n, _ in res)

kinds = sys.argv[1:] or ["pose", "hand"]
rows, raw = [], {}
for kind in kinds:
    for track in (0.5, 0.9):
        for name, (pre, post) in SEQS.items():
            cont = run(kind, RunningMode.VIDEO, track, pre + post)
            tail = cont[len(pre):]
            fresh = run(kind, RunningMode.VIDEO, track, post)
            img = run(kind, RunningMode.IMAGE, track, post)
            row = dict(kind=kind, track=track, seq=name,
                       pre_found=sum(1 for n, _ in cont[:30] if n), gap_found=sum(1 for n, _ in cont[30:len(pre)] if n),
                       cont_first=first_found(tail), cont_found=sum(1 for n, _ in tail if n),
                       fresh_first=first_found(fresh), fresh_found=sum(1 for n, _ in fresh if n),
                       img_first=first_found(img), img_found=sum(1 for n, _ in img if n), n_after=len(post),
                       cont_cx_after=[c for _, c in tail[:5]], fresh_cx_after=[c for _, c in fresh[:5]])
            rows.append(row); raw[f"{kind}|{track}|{name}"] = dict(cont=s(cont), fresh=s(fresh), image=s(img), cont_cx=[c for _, c in cont], fresh_cx=[c for _, c in fresh])
            print(json.dumps(row), flush=True)
            print("   cont :", s(cont[:len(pre)]), "|", s(tail)); print("   fresh:", " " * len(pre), "|", s(fresh))
            print("   image:", " " * len(pre), "|", s(img), flush=True)
(OUT / f"results_{'_'.join(kinds)}.json").write_text(json.dumps(dict(rows=rows, raw=raw), indent=1))
