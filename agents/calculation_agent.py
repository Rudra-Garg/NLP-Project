import numexpr

from .base_agent import IAgent


class CalculationAgent(IAgent):
    """An agent responsible for evaluating mathematical expressions."""

    def get_name(self) -> str:
        return "calculation"

    def execute(self, intent: dict) -> str:
        action = intent.get("action")
        params = intent.get("parameters", {})
        expression = params.get("expression")

        if action != "evaluate_expression":
            return "I don't know how to perform that calculation action."

        if not expression:
            return "You asked me to calculate something, but didn't provide an expression."

        print(f"[CalculationAgent] Evaluating expression: '{expression}'")

        try:
            # Use numexpr to safely evaluate the expression
            result = numexpr.evaluate(expression)
            # Use .item() to convert numpy types to native Python types
            answer = f"The answer is {result.item()}"
            print(f"[CalculationAgent] Evaluation successful. Responding with: \"{answer}\"")
            return answer
        except Exception as e:
            print(f"[CalculationAgent] ERROR: numexpr failed to evaluate '{expression}': {e}")
            return "I'm sorry, I couldn't understand that math expression."
