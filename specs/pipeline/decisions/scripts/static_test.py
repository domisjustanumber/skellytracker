"""Static A-pose image repeated: person x30, gap x30, person x60, VIDEO mode vs fresh."""
import cv2, numpy as np, mediapipe as mp
from pathlib import Path
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, HandLandmarker, HandLandmarkerOptions, RunningMode
M = Path.home() / ".freemocap" / "skellytracker-models"
img = cv2.cvtColor(cv2.imread(str(Path.home() / ".cache/skellytracker/test_images/5dd35b2f0f11.jpg")), cv2.COLOR_BGR2RGB)
H, W = img.shape[:2]
gaps = {"black": np.zeros_like(img), "blur": cv2.GaussianBlur(img, (0, 0), 40),
        "shift40": None}
def build(kind, track):
    if kind == "pose":
        return PoseLandmarker.create_from_options(PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(M / "d9347aa2_pose_landmarker_heavy.task")),
            running_mode=RunningMode.VIDEO, num_poses=1, min_pose_detection_confidence=0.5, min_pose_presence_confidence=0.5, min_tracking_confidence=track))
    return HandLandmarker.create_from_options(HandLandmarkerOptions(base_options=BaseOptions(model_asset_path=str(M / "de73a113_hand_landmarker.task")),
        running_mode=RunningMode.VIDEO, num_hands=2, min_hand_detection_confidence=0.5, min_hand_presence_confidence=0.5, min_tracking_confidence=track))
def run(kind, track, seq):
    lm = build(kind, track); out = []
    try:
        for i, a in enumerate(seq):
            r = lm.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(a)), i * 33)
            L = r.pose_landmarks if kind == "pose" else r.hand_landmarks
            out.append(str(min(len(L), 9)) if L else ".")
    finally:
        lm.close()
    return "".join(out)
shifted = cv2.warpAffine(img, np.float32([[1, 0, 0.4 * W], [0, 1, 0]]), (W, H))
for kind in ("pose", "hand"):
    for track in (0.5, 0.9):
        for g, gimg in gaps.items():
            if g == "shift40":
                seq_pre, post = [img] * 30, [shifted] * 60
            else:
                seq_pre, post = [img] * 30 + [gimg] * 30, [img] * 60
            c = run(kind, track, seq_pre + post); f = run(kind, track, post)
            print(f"{kind} t={track} {g:8s} cont: {c[:len(seq_pre)]} | {c[len(seq_pre):]}", flush=True)
            print(f"{kind} t={track} {g:8s} fresh:{' ' * len(seq_pre)} | {f}", flush=True)
