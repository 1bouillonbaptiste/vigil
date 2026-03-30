from typing import Protocol, TypeAlias

import numpy as np
import numpy.typing as npt

from vigil.embedding.business_logic.models.embedded_track import Embedding

ImageData: TypeAlias = npt.NDArray[np.uint8]


class EmbeddingModel(Protocol):
    """Abstract embedding model."""

    def embed(self, description: str) -> Embedding:
        """Compute and return a text embedding."""
        ...

    def embed_image(self, data: ImageData) -> Embedding:
        """Compute and return an image embedding."""
        ...
