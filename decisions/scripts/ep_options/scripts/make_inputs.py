"""Make the .npy inputs once (needs Pillow). Usage: python -I -B make_inputs.py IMAGE OUT_DIR

YOLOX: BGR, letterbox 640x640, pad 114 top-left, raw 0-255 float32, NCHW.
RTMW: RGB, 288x384 (WxH) crop around the person box of the pinned image, ImageNet mean/std, NCHW.
Batch 3 stacks three different inputs: original, horizontal flip, shifted crop.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MEAN = np.array([123.675, 116.28, 103.53], np.float32)
STD = np.array([58.395, 57.12, 57.375], np.float32)
PERSON_BOX = (60, 40, 560, 860)  # same box as the device-check suite (x0, y0, x1, y1)


def letterbox(image, size=640):
    scale = size / max(image.size)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.BILINEAR)
    canvas = np.full((size, size, 3), 114, np.float32)
    canvas[: resized.height, : resized.width] = np.asarray(resized, np.float32)
    return canvas[..., ::-1].transpose(2, 0, 1).copy()  # RGB -> BGR, HWC -> CHW


def person_crop(image, box, height=384, width=288):
    x0, y0, x1, y1 = box
    cx, cy, box_h = (x0 + x1) / 2, (y0 + y1) / 2, y1 - y0
    box_w = max(x1 - x0, box_h * width / height)
    box_h = box_w * height / width
    b = (cx - box_w / 2, cy - box_h / 2, cx + box_w / 2, cy + box_h / 2)
    crop = image.crop(tuple(round(v) for v in b)).resize((width, height), Image.BILINEAR)
    return ((np.asarray(crop, np.float32) - MEAN) / STD).transpose(2, 0, 1).copy()


def main():
    image = Image.open(sys.argv[1]).convert("RGB")
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    flipped = image.transpose(Image.FLIP_LEFT_RIGHT)
    w = image.width
    x0, y0, x1, y1 = PERSON_BOX
    fbox = (w - x1, y0, w - x0, y1)
    sbox = (x0 + 40, y0 + 30, x1 + 40, y1 + 30)
    shifted = image.crop((60, 40, image.width, image.height))

    yolox = [letterbox(image), letterbox(flipped), letterbox(shifted)]
    rtmw = [person_crop(image, PERSON_BOX), person_crop(flipped, fbox), person_crop(image, sbox)]
    if "--b6" in sys.argv:  # six different YOLOX inputs; b1/b3 files are not touched
        flip_shift = flipped.crop((0, 40, flipped.width - 60, flipped.height))
        zoom = image.crop((0, 100, image.width, 1000))
        yolox6 = yolox + [letterbox(flip_shift), letterbox(zoom), letterbox(image.rotate(5, fillcolor=(114, 114, 114)))]
        np.save(out / "yolox_b6.npy", np.stack(yolox6).astype(np.float32))
        print("yolox_b6.npy", np.load(out / "yolox_b6.npy").shape)
        return
    for name, items in (("yolox", yolox), ("rtmw", rtmw)):
        np.save(out / f"{name}_b1.npy", np.stack(items[:1]).astype(np.float32))
        np.save(out / f"{name}_b3.npy", np.stack(items).astype(np.float32))
    for p in sorted(out.glob("*.npy")):
        a = np.load(p)
        print(p.name, a.shape, a.dtype, float(a.min()), float(a.max()))


if __name__ == "__main__":
    main()
