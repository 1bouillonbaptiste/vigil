from pathlib import Path
from typing import Final

import torch
from transformers import CLIPModel, CLIPTokenizer

from vigil.embedding.business_logic.models.embedded_track import Embedding

_MODELS_DIR: Final[Path] = Path(__file__).parent / "models"
_CLIP_MODEL_NAME: Final[str] = "openai/clip-vit-base-patch32"


class ClipEmbeddingModel:
    """EmbeddingModel adapter backed by CLIP ViT-B/32 text encoder.

    On first instantiation the model weights are downloaded from
    HuggingFace and stored in the ``models/`` directory next to this
    file.  Subsequent instantiations load from that directory without
    network access.
    """

    def __init__(self) -> None:
        _MODELS_DIR.mkdir(exist_ok=True)
        self._tokenizer: CLIPTokenizer = CLIPTokenizer.from_pretrained(  # type: ignore[assignment]
            _CLIP_MODEL_NAME, cache_dir=_MODELS_DIR
        )
        self._model: CLIPModel = CLIPModel.from_pretrained(  # type: ignore[assignment]
            _CLIP_MODEL_NAME, cache_dir=_MODELS_DIR
        )
        self._model.eval()

    def embed(self, description: str) -> Embedding:
        """Return a normalized CLIP text embedding for the given description."""
        inputs = self._tokenizer(description, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            features: torch.Tensor = self._model.get_text_features(**inputs)
        normalized = features / features.norm(dim=-1, keepdim=True)
        return Embedding(tuple(float(x) for x in normalized.squeeze().cpu().numpy()))
