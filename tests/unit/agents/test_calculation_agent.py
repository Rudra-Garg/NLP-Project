import pytest

from agents import CalculationAgent


@pytest.fixture
def agent():
    return CalculationAgent()


def test_evaluate_simple_expression(agent):
    intent = {
        "action": "evaluate_expression",
        "parameters": {"MATH_EXPRESSION": "two plus two"}
    }
    response = agent.execute(intent)
    assert "The answer is 4" in response


def test_evaluate_complex_expression(agent):
    intent = {
        "action": "evaluate_expression",
        "parameters": {"MATH_EXPRESSION": "100 divided by ( 2 times 5 )"}
    }
    response = agent.execute(intent)
    assert "The answer is 10" in response


def test_missing_expression(agent):
    intent = {"action": "evaluate_expression", "parameters": {}}
    response = agent.execute(intent)
    assert "didn't provide an expression" in response


def test_invalid_expression(agent):
    intent = {
        "action": "evaluate_expression",
        "parameters": {"MATH_EXPRESSION": "this is not math"}
    }
    response = agent.execute(intent)
    assert "couldn't understand that math expression" in response


def test_wrong_action(agent):
    intent = {"action": "some_other_action", "parameters": {}}
    response = agent.execute(intent)
    assert "don't know how to perform that calculation action" in response
