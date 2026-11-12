"""Evidence of ADR-G79P: the pixel centres of cv2.resize and cv2.warpAffine.

Run: uv run python specs/model-sidecar/decisions/scripts/G79P_pixel_centres.py
It prints the ramp of the entry, the difference of the sampled source positions at five scales and
the difference between the mmpose inverse (mmpose v1.3.2 `topdown.py:154-156`, transcribed) and
`M^-1`, the `INTER_NEAREST` rule of `cv2.resize` and the `INTER_AREA` result of `cv2.warpAffine`.
It writes no file.
"""

import cv2
import numpy as np


def sampled(src_n: int, dst_n: int, x: int) -> tuple[float, float]:
    """The source index that destination pixel `x` samples: cv2.resize, then cv2.warpAffine."""
    s = dst_n / src_n
    index = np.arange(src_n, dtype=np.float32)[None, :]
    resized = cv2.resize(index, (dst_n, 1), interpolation=cv2.INTER_LINEAR)
    warped = cv2.warpAffine(index, np.float64([[s, 0, 0], [0, 1, 0]]), (dst_n, 1),
                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return float(resized[0, x]), float(warped[0, x])


def main() -> None:
    print("OpenCV", cv2.__version__)
    ramp = np.float32([[0, 10, 20, 30]])
    resized = cv2.resize(ramp, (8, 1), interpolation=cv2.INTER_LINEAR)
    warped = cv2.warpAffine(ramp, np.float64([[2, 0, 0], [0, 1, 0]]), (8, 1),
                            flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    print("ramp x=1: cv2.resize", float(resized[0, 1]), "cv2.warpAffine", float(warped[0, 1]))

    for src_n, dst_n in [(4, 8), (100, 50), (300, 100), (625, 320), (10, 64)]:
        s = dst_n / src_n
        a, b = sampled(src_n, dst_n, dst_n // 2)
        print(f"s={s:.6f}: resize - warpAffine = {a - b:+.6f}, 0.5 * (1 / s - 1) = {0.5 * (1 / s - 1):+.6f}")

    # The affine_person_crop M of the vector case tall-box-grows-width.
    center, size, target = np.float64([200, 250]), np.float64([375, 500]), np.float64([192, 256])
    m = np.float64([[0.512, 0, -6.4], [0, 0.512, 0]])
    m_inv = cv2.invertAffineTransform(m)
    xy = np.float64([[96, 128], [0, 0], [192, 256], [10.25, 3.5]])
    mmpose = xy / target * size + center - 0.5 * size
    print("max |mmpose inverse - M^-1| =", float(np.abs((m_inv[:, :2] @ xy.T + m_inv[:, 2:]).T - mmpose).max()))

    # cv2.INTER_NEAREST takes floor(x * src_n / dst_n); INTER_NEAREST_EXACT is the half-pixel rule.
    index = np.arange(10, dtype=np.float32)[None, :]
    for name, flag in [("INTER_NEAREST", cv2.INTER_NEAREST), ("INTER_NEAREST_EXACT", cv2.INTER_NEAREST_EXACT)]:
        print("10 -> 4", name, cv2.resize(index, (4, 1), interpolation=flag)[0].tolist())

    # cv2.warpAffine runs INTER_AREA as INTER_LINEAR.
    img = np.random.default_rng(0).random((100, 100), dtype=np.float32)
    down = np.float64([[0.3, 0, 0], [0, 0.3, 0]])
    area, linear = (cv2.warpAffine(img, down, (30, 30), flags=f) for f in (cv2.INTER_AREA, cv2.INTER_LINEAR))
    print("cv2.warpAffine INTER_AREA == INTER_LINEAR:", bool(np.array_equal(area, linear)))


if __name__ == "__main__":
    main()
