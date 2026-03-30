import numpy as np
import numpy.typing as npt


class Image:
    """Wrapper for raw image data."""

    def __init__(self, data: npt.NDArray[np.uint8]) -> None:
        self._data = data

    def numpy(self) -> npt.NDArray[np.uint8]:
        """Return the underlying uint8 image data."""
        return self._data
