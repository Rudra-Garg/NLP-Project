import json
from pathlib import Path

import pytest

from intent import FastClassifier

# Define a small, controlled set of intents for testing
TEST_INTENTS = [
    {"text": "launch notepad", "type": "system_control", "action": "launch_application"},
    {"text": "open calculator", "type": "system_control", "action": "launch_application"},
    {"text": "can you launch notepad", "type": "system_control", "action": "launch_application"},
    {"text": "please open chrome", "type": "system_control", "action": "launch_application"},
    {"text": "calculate 2 plus 2", "type": "calculation", "action": "evaluate_expression"},
    {"text": "what is 10 times 5", "type": "calculation", "action": "evaluate_expression"},
    {"text": "calculate what is 10 x 5", "type": "calculation", "action": "evaluate_expression"},
    {"text": "what is 5 times 10", "type": "calculation", "action": "evaluate_expression"},
    {"text": "compute 100 divided by 20", "type": "calculation", "action": "evaluate_expression"}
]


@pytest.fixture(scope="module")
def fast_classifier_instance(tmpdir_factory):
    """
    Creates an instance of FastClassifier with a temporary intents file.
    This runs once per module, making tests faster.
    """
    # Create a temporary directory and a dummy intents file
    temp_dir = tmpdir_factory.mktemp("data")
    intents_path = Path(temp_dir) / "test_intent_data.json"
    with open(intents_path, 'w') as f:
        json.dump(TEST_INTENTS, f)

    # Initialize the classifier with this dummy data
    # NOTE: Ensure the model name matches what's in your .env or is downloadable
    # Using a smaller model for testing can speed things up.
    model_name = "all-MiniLM-L6-v2"
    classifier = FastClassifier(
        intents_path=intents_path,
        model_name=model_name,
        threshold=0.70
    )
    return classifier


def test_high_confidence_match(fast_classifier_instance):
    """
    Test that a very similar phrase correctly classifies with high confidence.
    """
    transcript = "can you launch notepad"
    result = fast_classifier_instance.classify(transcript)
    assert result['type'] == 'system_control'
    assert result['action'] == 'launch_application'
    assert result['confidence'] > 0.70


def test_calculation_match(fast_classifier_instance):
    """
    Test that a calculation-related phrase is correctly identified.
    """
    transcript = "calculate what is 10 x 5"
    result = fast_classifier_instance.classify(transcript)
    assert result['type'] == 'calculation'
    assert result['action'] == 'evaluate_expression'
    assert result['confidence'] > 0.70


def test_low_confidence_rejection(fast_classifier_instance):
    """
    Test that an out-of-domain phrase is correctly classified as 'unknown'.
    """
    transcript = "what is the weather like in london"
    result = fast_classifier_instance.classify(transcript)
    assert result['type'] == 'unknown'


def test_empty_transcript(fast_classifier_instance):
    """
    Test that an empty transcript is handled gracefully.
    """
    transcript = ""
    result = fast_classifier_instance.classify(transcript)
    assert result['type'] == 'unknown'
    assert result['confidence'] == 0.0
