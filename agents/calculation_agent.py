import numexpr

from .base_agent import IAgent


class CalculationAgent(IAgent):
    # Mapping for text numbers to digits
    TEXT_TO_NUMBER = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
        "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
        "eighty": "80", "ninety": "90", "hundred": "100", "thousand": "1000"
    }

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
        expression = expression.lower()

        # Convert text numbers to digits
        for word, digit in self.TEXT_TO_NUMBER.items():
            expression = expression.replace(word, digit)

        # Replace words with symbols
        expression = expression.replace("plus", "+").replace("minus", "-")
        expression = expression.replace("times", "*").replace("divided by", "/")
        expression = expression.replace("x", "*")  # common spoken alternative for 'times'

        # Remove extra spaces
        expression = " ".join(expression.split())

        print(f"[CalculationAgent] Evaluating cleaned expression: '{expression}'")

        # Check if the expression contains non-mathematical words (basic validation)
        # After all replacements, only numbers, operators, spaces, and parentheses should remain
        import re
        if re.search(r'[a-zA-Z]{2,}', expression):
            # Still contains words with 2+ letters - probably not a valid math expression
            print(f"[CalculationAgent] ERROR: Expression still contains text words: '{expression}'")
            return "I'm sorry, I couldn't understand that math expression."

        try:
            result = numexpr.evaluate(expression)
            answer = f"The answer is {result.item()}"
            print(f"[CalculationAgent] Evaluation successful. Responding with: \"{answer}\"")
            return answer
        except Exception as e:
            print(f"[CalculationAgent] ERROR: numexpr failed to evaluate '{expression}': {e}")
            return "I'm sorry, I couldn't understand that math expression."
