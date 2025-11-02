from unittest.mock import patch

import pytest

from agents import SystemControlAgent


@pytest.fixture
def agent():
    return SystemControlAgent()


@patch('subprocess.Popen')
def test_launch_application_success(mock_popen, agent):
    intent = {
        "action": "launch_application",
        "parameters": {"APP_NAME": "Notepad"}
    }
    response = agent.execute(intent)

    # Check that Popen was called with the lowercase, space-removed command
    mock_popen.assert_called_once_with("notepad")
    assert response == "Okay, launching Notepad."


@patch('subprocess.Popen')
def test_launch_application_not_found(mock_popen, agent):
    mock_popen.side_effect = FileNotFoundError

    intent = {
        "action": "launch_application",
        "parameters": {"APP_NAME": "some_fake_app"}
    }
    response = agent.execute(intent)
    assert "couldn't find an application named some_fake_app" in response


def test_missing_app_name(agent):
    intent = {"action": "launch_application", "parameters": {}}
    response = agent.execute(intent)
    assert "didn't catch the name" in response
