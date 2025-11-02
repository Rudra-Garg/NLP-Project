from pathlib import Path
from unittest.mock import patch

import pytest

from agent_manager import AgentManager
from agents import CalculationAgent, SystemControlAgent
from intent import FastClassifier
from ner_predictor import NERPredictor


# This is a simplified version of the main processing logic for testing
def process_command(transcription, fast_classifier, ner_predictor, agent_manager):
    """
    Simulates the core NLP pipeline from transcript to agent response.
    LLM fallback is not included here; it can be tested separately
    or by adding mock objects.
    """
    intent = fast_classifier.classify(transcription)

    if intent.get('type') != 'unknown':
        entities = ner_predictor.predict(transcription)
        intent.setdefault('parameters', {}).update(entities)

    return agent_manager.dispatch(intent)


@pytest.fixture(scope="module")
def nlp_pipeline():
    """
    Sets up the full NLP pipeline for integration testing.
    """
    project_root = Path(__file__).parents[2]

    # 1. Fast Classifier (using real data)
    intents_json_path = project_root / "data" / "intent_training_data.json"
    if not intents_json_path.exists():
        pytest.skip("intent_training_data.json not found. Run generate_intent_data.py.")

    fast_classifier = FastClassifier(
        intents_path=intents_json_path,
        model_name="all-MiniLM-L6-v2",
        threshold=0.70
    )

    # 2. NER Predictor
    ner_model_path = project_root / "models" / "ner" / "ner_model.joblib"
    if not ner_model_path.exists():
        pytest.skip("ner_model.joblib not found. Run train_ner_model.py.")
    ner_predictor = NERPredictor(ner_model_path)

    # 3. Agent Manager
    agent_manager = AgentManager()
    agent_manager.register_agent(CalculationAgent())
    agent_manager.register_agent(SystemControlAgent())

    return fast_classifier, ner_predictor, agent_manager


@patch('subprocess.Popen')
def test_end_to_end_launch_app(mock_popen, nlp_pipeline):
    """
    Tests the full pipeline for a system control command.
    Transcript -> FastClassifier -> NER -> AgentManager -> SystemControlAgent
    """
    fast_classifier, ner_predictor, agent_manager = nlp_pipeline

    transcript = "hey loki launch notepad"
    response = process_command(transcript, fast_classifier, ner_predictor, agent_manager)

    assert "Okay, launching notepad" in response
    mock_popen.assert_called_once_with("notepad")


def test_end_to_end_calculation(nlp_pipeline):
    """
    Tests the full pipeline for a calculation command.
    Transcript -> FastClassifier -> NER -> AgentManager -> CalculationAgent
    """
    fast_classifier, ner_predictor, agent_manager = nlp_pipeline

    transcript = "could you please calculate ten times three"
    response = process_command(transcript, fast_classifier, ner_predictor, agent_manager)

    assert "The answer is 30" in response


def test_end_to_end_unhandled_intent(nlp_pipeline):
    """
    Tests that an unknown command flows through and gets the default response.
    """
    fast_classifier, ner_predictor, agent_manager = nlp_pipeline

    transcript = "what is the meaning of life"
    response = process_command(transcript, fast_classifier, ner_predictor, agent_manager)

    assert "I'm not sure what you mean" in response
