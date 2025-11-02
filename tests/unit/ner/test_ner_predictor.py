from pathlib import Path

import pytest

from ner_predictor import NERPredictor


@pytest.fixture(scope="module")
def ner_predictor_instance():
    """
    Loads the NERPredictor with the trained model.
    Assumes the model exists at the expected path.
    """
    project_root = Path(__file__).parents[3]  # Go up to the project root from tests/unit/ner
    model_path = project_root / "models" / "ner" / "ner_model.joblib"
    if not model_path.exists():
        pytest.skip("NER model not found. Run train_ner_model.py to create it.")
    return NERPredictor(model_path)


@pytest.mark.parametrize("transcript, expected_entities", [
    ("can you launch google chrome for me", {"APP_NAME": "google chrome"}),
    ("please calculate what is 25 times ( 4 plus 3 )", {"MATH_EXPRESSION": "25 times ( 4 plus 3 )"}),
    ("open the task manager", {"APP_NAME": "task manager"}),
    ("what is the square root of 81", {"MATH_EXPRESSION": "square root of 81"}),
    ("what time is it", {}),  # No entities
    ("run notepad++", {"APP_NAME": "notepad++"}),
])
def test_entity_extraction(ner_predictor_instance, transcript, expected_entities):
    """
    Tests the NER model against a variety of transcripts.
    """
    entities = ner_predictor_instance.predict(transcript)
    assert entities == expected_entities
