"""Evidence of PHJ3: a uint8 resize against a float32 resize, and the order of /255 and the resize or warp.

Run: uv run python specs/model-sidecar/decisions/scripts/resize_compute_dtype_probe.py
It needs only OpenCV and NumPy. It reads and writes no file.
"""

import cv2
import numpy as np

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)
FILTERS = {"linear": cv2.INTER_LINEAR, "area": cv2.INTER_AREA, "cubic": cv2.INTER_CUBIC, "nearest": cv2.INTER_NEAREST}


def roboflow_resize(source, out_h, out_w, coord_dtype=np.float32):
    """Text copy of Roboflow-Exporter onnx_runtime/preprocess.py:22-55 at d0559b9 ((K, H, W) float32).

    `coord_dtype` float64 is the one change, to show the source of a small difference.
    """
    src_h, src_w = source.shape[-2], source.shape[-1]
    src_y = np.clip((np.arange(out_h, dtype=coord_dtype) + 0.5) * (src_h / out_h) - 0.5, 0.0, src_h - 1)
    src_x = np.clip((np.arange(out_w, dtype=coord_dtype) + 0.5) * (src_w / out_w) - 0.5, 0.0, src_w - 1)
    y0, x0 = np.floor(src_y).astype(np.int64), np.floor(src_x).astype(np.int64)
    y1, x1 = np.minimum(y0 + 1, src_h - 1), np.minimum(x0 + 1, src_w - 1)
    dy, dx = (src_y - y0)[:, None], (src_x - x0)[None, :]
    if 3 * src_h < 4 * out_h:
        horizontal = (1 - dx) * np.take(source, x0, axis=-1) + dx * np.take(source, x1, axis=-1)
        output = (1 - dy) * horizontal[..., y0, :] + dy * horizontal[..., y1, :]
    else:
        a, b = source[..., y0[:, None], x0[None, :]], source[..., y0[:, None], x1[None, :]]
        c, d = source[..., y1[:, None], x0[None, :]], source[..., y1[:, None], x1[None, :]]
        output = (1 - dy) * ((1 - dx) * a + dx * b) + dy * ((1 - dx) * c + dx * d)
    return np.asarray(output, dtype=np.float32)


def roboflow_host(rgb_u8, h, w):
    """Roboflow order (preprocess.py:75-85): /255, float resize, (x - mean) / std."""
    chw = roboflow_resize((rgb_u8.astype(np.float32) / 255.0).transpose(2, 0, 1), h, w)
    return (chw - MEAN[:, None, None]) / STD[:, None, None]


def spec_imagenet(resized_hwc):
    """`imagenet` of pre.normalize on 0-255 values, CHW."""
    return ((resized_hwc.astype(np.float32) - MEAN * 255) / (STD * 255)).transpose(2, 0, 1)


def main():
    rng = np.random.default_rng(0)
    print("OpenCV", cv2.__version__, "NumPy", np.__version__)

    ramp = np.array([[0, 10, 20, 30]], np.uint8)
    print("1. ramp [0, 10, 20, 30], 2x linear upscale to 8")
    print("   uint8  :", cv2.resize(ramp, (8, 1), interpolation=cv2.INTER_LINEAR)[0].tolist())
    print("   float32:", cv2.resize(ramp.astype(np.float32), (8, 1), interpolation=cv2.INTER_LINEAR)[0].tolist())

    print("2. random 480x640x3 to 560x560: order of /255 (float32) and uint8 against float32")
    noise = rng.integers(0, 256, (480, 640, 3), dtype=np.uint8)
    for name, flag in FILTERS.items():
        f = noise.astype(np.float32)
        after = cv2.resize(f, (560, 560), interpolation=flag) / 255.0
        before = cv2.resize(f / 255.0, (560, 560), interpolation=flag)
        u8 = cv2.resize(noise, (560, 560), interpolation=flag).astype(np.float32) / 255.0
        print(f"   {name:7s} order max {np.abs(after - before).max():.1e}; uint8-float32 max "
              f"{np.abs(u8 - after).max() * 255:.3f} (0-255); float32 range "
              f"[{after.min() * 255:.2f}, {after.max() * 255:.2f}]")

    print("3. Roboflow host against the spec (stretch, linear, imagenet, rgb) to 560x560")
    yy, xx = np.mgrid[0:480, 0:640]
    gradient = np.stack([xx * 255 / 639, yy * 255 / 479, (xx + yy) * 255 / 1118], -1).round().astype(np.uint8)
    for label, image in [("gradient 480x640", gradient), ("noise 480x640", noise)]:
        rf = roboflow_host(image, 560, 560)
        for dtype in ("float32", "uint8"):
            src = image.astype(np.float32) if dtype == "float32" else image
            d = np.abs(rf - spec_imagenet(cv2.resize(src, (560, 560), interpolation=cv2.INTER_LINEAR)))
            print(f"   {label}: compute_dtype {dtype:7s} max {d.max():.2e}, mean {d.mean():.2e}")
    print(f"   one uint8 step after the G/B std is {1 / (255 * 0.225):.2e}")

    print("4. noise 1080x1920 to 560x560: Roboflow resize against cv2 float32, by coordinate dtype")
    big = rng.integers(0, 256, (1080, 1920, 3), dtype=np.uint8).astype(np.float32)
    cv = cv2.resize(big, (560, 560), interpolation=cv2.INTER_LINEAR)
    for coord in (np.float32, np.float64):
        rf = roboflow_resize(big.transpose(2, 0, 1), 560, 560, coord).transpose(1, 2, 0)
        print(f"   {coord.__name__} coordinates: max {np.abs(rf - cv).max():.2e} (0-255)")

    print("5. noise 300x500 warpAffine (1.1x, border 114): order of /255 with the border value scaled too")
    small = rng.integers(0, 256, (300, 500, 3), dtype=np.uint8).astype(np.float32)
    warp = np.array([[1.1, 0.0, -20.0], [0.0, 1.1, -10.0]], np.float32)
    for name, flag in FILTERS.items():
        after = cv2.warpAffine(small, warp, (560, 340), flags=flag, borderValue=(114,) * 3) / 255.0
        before = cv2.warpAffine(small / 255.0, warp, (560, 340), flags=flag, borderValue=(114 / 255,) * 3)
        print(f"   {name:7s} order max {np.abs(after - before).max():.1e}")


if __name__ == "__main__":
    main()
