"""Typed errors for RTMPoseSession batch inference."""


class BatchSizeMismatchError(ValueError):
    """predict_batch received a non-empty image list that does not match session batch_size."""

    def __init__(self, *, actual: int, expected: int, message: str | None = None) -> None:
        self.actual = actual
        self.expected = expected
        super().__init__(
            message
            or f"predict_batch expected {expected} images (session batch_size), got {actual}"
        )
