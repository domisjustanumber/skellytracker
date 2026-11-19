# Evidence of ADR-S1TG. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
"""Serial vs pooled cv2.imdecode of synthetic JPEGs under a restricted CPU affinity (emulates a small machine)."""
import concurrent.futures as cf, statistics, sys, time  # noqa: E401
import cv2, numpy as np, psutil  # noqa: E401

rng = np.random.default_rng(0)
def synth(w, h):
    y, x = np.mgrid[0:h, 0:w]
    img = np.stack([(x * 255 // w), (y * 255 // h), ((x + y) % 256)], -1).astype(np.uint8)
    img = cv2.GaussianBlur(cv2.add(img, rng.integers(0, 60, img.shape, dtype=np.uint8)), (3, 3), 0)
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 90])[1].tobytes()

flags = cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION
dec = lambda b: cv2.imdecode(np.frombuffer(b, np.uint8), flags)  # noqa: E731
proc = psutil.Process()
iters = 150
for w, h in ((1280, 720), (1920, 1080)):
    bufs = [synth(w, h) for _ in range(6)]
    print(f"{w}x{h} mean size {sum(map(len, bufs)) // 6 // 1024} KiB", flush=True)
    for cores in (2, 4):
        proc.cpu_affinity(list(range(cores)))
        for n in (3, 6):
            b = bufs[:n]
            serial = [dec(x) for x in b]
            with cf.ThreadPoolExecutor(max_workers=min(n, cores)) as pool:
                pooled = [f.result() for f in [pool.submit(dec, x) for x in b]]
                assert all(np.array_equal(a, c) for a, c in zip(serial, pooled))  # noqa: B905, S101
                res = {}
                for name, fn in (("serial", lambda: [dec(x) for x in b]),  # noqa: B023
                                 ("pool", lambda: [f.result() for f in [pool.submit(dec, x) for x in b]])):  # noqa: B023
                    for _ in range(10): fn()  # noqa: E701
                    walls = []; c0 = time.process_time()  # noqa: E702
                    for _ in range(iters):
                        t = time.perf_counter(); fn(); walls.append((time.perf_counter() - t) * 1e3)  # noqa: E702
                    res[name] = (statistics.median(walls), (time.process_time() - c0) * 1e3 / iters)
            s, p = res["serial"], res["pool"]
            print(f"  cores={cores} N={n} workers={min(n, cores)}: serial wall {s[0]:.2f} cpu {s[1]:.2f} | pool wall {p[0]:.2f} cpu {p[1]:.2f} ms | x{s[0] / p[0]:.2f}", flush=True)
proc.cpu_affinity(list(range(psutil.cpu_count())))
print("cores", psutil.cpu_count(), "cv2", cv2.__version__, "py", sys.version.split()[0])
