# Decision log: evidence entries

These entries are `evidence`: measurements. They are not in the read path. Scan these rows before
you make a measurement, and read the entries that apply ([Rules](../../../decisions/README.md#rules)). An entry that an
accepted entry uses, or that a later measurement replaces, is in [historical.md](historical.md).

### Evidence

| # | Decision | Status |
|---|----------|--------|
| [6JWJ](entries/6JWJ-mediapipe-video-landmarker-does-not-stick.md) | A MediaPipe VIDEO-mode landmarker finds a person again after a gap; `mediapipe_tasks` has no reset; run again on MediaPipe 1.2.2 | evidence |
