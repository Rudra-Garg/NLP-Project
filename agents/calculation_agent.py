import numexpr

from .base_agent import IAgent


class CalculationAgent(IAgent):
    def get_name(self) -> str:
        return "calculation"

    def execute(self, intent: dict) -> str:
        action = intent.get("action")
        params = intent.get("parameters", {})

        # The expression is now passed as a parameter from the NER model
        expression = params.get("MATH_EXPRESSION")

        if action != "evaluate_expression":
            return "I don't know how to perform that calculation action."

        if not expression:
            return "You asked me to calculate something, but didn't provide an expression."

        # Clean up the expression for numexpr
        # Replace words with symbols
        expression = expression.lower().replace("plus", "+").replace("minus", "-")
        expression = expression.replace("times", "*").replace("divided by", "/")
        expression = expression.replace("x", "*")  # common spoken alternative for 'times'

        print(f"[CalculationAgent] Evaluating cleaned expression: '{expression}'")

        try:
            result = numexpr.evaluate(expression)
            answer = f"The answer is {result.item()}"
            print(f"[CalculationAgent] Evaluation successful. Responding with: \"{answer}\"")
            return answer
        except Exception as e:
            print(f"[CalculationAgent] ERROR: numexpr failed to evaluate '{expression}': {e}")
            return "I'm sorry, I couldn't understand that math expression."
