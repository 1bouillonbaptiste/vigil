from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class Image:
    """Wrapper for raw image data."""

    _data: npt.NDArray[np.uint8]
