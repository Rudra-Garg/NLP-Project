import json
from unittest.mock import patch

import pytest

from intent import LLMClassifier


@pytest.fixture
def llm_classifier():
    """Returns an instance of the LLMClassifier for testing."""
    return LLMClassifier(model_name="test-model")


@patch('ollama.chat')
def test_successful_classification(mock_ollama_chat, llm_classifier):
    """
    Test that the LLMClassifier correctly parses a valid JSON response from the mock LLM.
    """
    # Define the mock response from ollama.chat
    mock_response = {
        'message': {
            'content': json.dumps({
                "type": "system_control",
                "action": "launch_application",
                "parameters": {"name": "notepad"},
                "confidence": 0.95
            })
        }
    }
    mock_ollama_chat.return_value = mock_response

    transcript = "please open notepad for me"
    result = llm_classifier.classify(transcript)

    # Assert that the correct data was returned
    assert result['type'] == 'system_control'
    assert result['action'] == 'launch_application'
    assert result['parameters']['name'] == 'notepad'
    assert result['confidence'] == 0.95
    assert result['transcript'] == transcript


@patch('ollama.chat')
def test_handles_json_error(mock_ollama_chat, llm_classifier):
    """
    Test that the classifier gracefully handles a malformed JSON response.
    """
    mock_response = {'message': {'content': '{"type": "calculation",, "action": "evaluate"}'}}  # Malformed JSON
    mock_ollama_chat.return_value = mock_response

    transcript = "some command"
    result = llm_classifier.classify(transcript)

    assert result['type'] == 'unknown'
    assert result['confidence'] == 0.0
    assert result['transcript'] == transcript


@patch('ollama.chat')
def test_handles_api_exception(mock_ollama_chat, llm_classifier):
    """
    Test that the classifier handles an exception from the ollama library.
    """
    mock_ollama_chat.side_effect = Exception("Ollama service not available")

    transcript = "some command"
    result = llm_classifier.classify(transcript)

    assert result['type'] == 'unknown'
    assert result['confidence'] == 0.0
    assert result['transcript'] == transcript
