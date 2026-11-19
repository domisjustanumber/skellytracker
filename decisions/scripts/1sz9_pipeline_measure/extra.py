# Evidence of ADR-1SZ9. This scratch script ran on 2026-11-18. A cleanup on 2026-11-19 replaced its local paths with environment variables. The logic did not change.
import json, sys  # noqa: E401, F401
sys.argv=['x']
exec(open('analyze.py').read().split('p(f"## Results equality')[0].split('# Main tables')[0])  # noqa: S102
import numpy as np  # noqa: E402
def load(t): return np.load(f'runs/{t}.npz')
src = open('analyze.py').read()
exec(src[src.index('def compare'):src.index('p(f"## Results equality')])  # noqa: S102
for a,b in [('X_repeat_M3','A_cuda_M3_720x3'),('X_huff_M3','A_cuda_M3_720x3'),('D_cuda_M2_720x3','D_cuda_M1_720x3')]:
    print(a,b,compare(load(b),load(a)))  # noqa: F821
for t,s in runs.items():  # noqa: F821
    if t.startswith('A_') and ('x6' in t or 'M3' in t):
        k=s['spans_keypoint_only']; print(t, 'wb.pre', round(k['wholebody.preprocess']['median'],2), 'wb.inf', round(k['wholebody.inference']['median'],2), 'p95', round(k['wall']['p95'],2), 'det', s['detector_calls'])  # noqa: E702
