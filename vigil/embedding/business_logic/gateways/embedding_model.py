from typing import Protocol

import numpy as np
import numpy.typing as npt

from vigil.embedding.business_logic.models.embedded_track import Embedding


class EmbeddingModel(Protocol):
    """Abstract embedding model."""

    def embed(self, description: str) -> Embedding:
        """Compute and return a text embedding."""
        ...

    def embed_image(self, data: npt.NDArray[np.uint8]) -> Embedding:
        """Compute and return an image embedding."""
        ...
