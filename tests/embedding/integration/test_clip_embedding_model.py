from pathlib import Path

import numpy as np
import pytest
from PIL import Image as PILImage

from vigil.embedding.adapters.secondary.clip_embedding_model import ClipEmbeddingModel
from vigil.embedding.business_logic.services.embedding_matcher import EmbeddingMatcher
from vigil.shared_kernel.models.image import Image

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


@pytest.fixture(scope="module")
def model() -> ClipEmbeddingModel:
    """Scope-level fixture to keep the model cached."""
    return ClipEmbeddingModel()


@pytest.fixture(scope="module")
def realistic_cat_image() -> Image:
    pil_image = PILImage.open(_DATA_DIR / "cat.jpg")
    return Image(np.array(pil_image, dtype=np.uint8))


def make_image(height: int = 64, width: int = 64) -> Image:
    return Image(np.zeros((height, width, 3), dtype=np.uint8))


def test_should_embed_text_description(model: ClipEmbeddingModel) -> None:
    embedding = model.embed("a person walking in the street")

    assert len(embedding.numpy()) == 512


def test_should_embed_image_batch(model: ClipEmbeddingModel) -> None:
    embeddings = model.embed_images([make_image(), make_image()])

    assert len(embeddings) == 2
    assert len(embeddings[0].numpy()) == 512


def test_pad_to_square_should_produce_square_image_with_black_fill() -> None:
    tall_narrow = PILImage.fromarray(np.ones((90, 30, 3), dtype=np.uint8) * 200)

    padded = ClipEmbeddingModel._pad_to_square(tall_narrow)

    assert padded.size == (90, 90)
    arr = np.array(padded)
    # original content is preserved in the center columns
    assert np.all(arr[:, 30:60] == 200)
    # padding columns are black
    assert np.all(arr[:, :15] == 0)
    assert np.all(arr[:, 75:] == 0)


def test_similar_descriptions_should_have_higher_similarity_than_dissimilar(model: ClipEmbeddingModel) -> None:
    cat = model.embed("a cat sitting on a mat")
    another_cat = model.embed("a cat resting on a rug")
    car = model.embed("a red sports car on the highway")

    assert cat.cosine(another_cat) > cat.cosine(car)


def test_cat_image_should_match_cat_description_with_high_probability(
    model: ClipEmbeddingModel, realistic_cat_image: Image
) -> None:
    neutral_embedding = model.embed("a random unrelated scene")
    matcher = EmbeddingMatcher(neutral_embedding=neutral_embedding)

    [cat_embedding] = model.embed_images([realistic_cat_image])

    cat_text = model.embed("a sitting cat and looking at me")
    car_text = model.embed("two blue cars")

    assert matcher.probability(cat_embedding, cat_text) > 0.9
    assert matcher.probability(cat_embedding, car_text) < 0.1
