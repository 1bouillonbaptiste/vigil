import math

from vigil.embedding.business_logic.models.embedded_track import Embedding


class EmbeddingMatcher:
    """Computes calibrated match probability via contrastive softmax.

    Scores an image embedding against a text embedding relative to a null
    embedding that represents "nothing in particular".  This turns the raw
    cosine similarity — which is not calibrated as an absolute value for
    cross-modal CLIP pairs — into a probability that is meaningful as a
    threshold: 0.5 means the image is equally close to the description and
    to the null, >0.5 means it leans toward the description.

    The temperature mirrors CLIP's learned logit scale (~100), making the
    softmax sharp enough to separate matches from non-matches.
    """

    def __init__(self, null_embedding: Embedding, temperature: float = 100.0) -> None:
        self._null = null_embedding
        self._temperature = temperature

    def probability(self, image_embedding: Embedding, text_embedding: Embedding) -> float:
        """Return P(image matches description) in [0, 1]."""
        score_match = image_embedding.cosine(text_embedding)
        score_null = image_embedding.cosine(self._null)
        return 1.0 / (1.0 + math.exp(self._temperature * (score_null - score_match)))
