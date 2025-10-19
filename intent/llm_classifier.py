import json

import ollama


class LLMClassifier:
    """
    A more advanced classifier that uses an Ollama LLM for intent recognition.
    It's slower but much more flexible than the FastClassifier.
    """

    def __init__(self, model_name: str):
        print(f"Initializing LLMClassifier with model '{model_name}'...")
        self.model_name = model_name
        # The system prompt is the most important part of making the LLM reliable.
        # It strictly tells the LLM to act like an API, not a chatbot.
        self.system_prompt = """
You are a non-conversational API. Your sole job is to read the user's utterance and emit exactly one valid JSON object. Do not output anything else.

Your JSON response MUST contain these four keys:
- "type": (string) one of "system_control", "calculation", "general", "unknown"
- "action": (string) one of "launch_application", "evaluate_expression", "get_time", "conversation"
- "parameters": (object) a dictionary of parameters, which is empty ({}) if none are found.
- "confidence": (float) your confidence in the classification, from 0.0 to 1.0.

If you do not understand the request, return a confidence of 0.1 and type "unknown".

EXAMPLES:
User: "can you open up notepad for me please"
{"type":"system_control","action":"launch_application","parameters":{"name":"notepad"},"confidence":0.9}

User: "calculate what 5 times 8 is"
{"type":"calculation","action":"evaluate_expression","parameters":{"expression":"5 * 8"},"confidence":1.0}

User: "what's the weather like"
{"type":"unknown","action":"","parameters":{},"confidence":0.1}

User: "kljdfg lkjfdg"
{"type":"unknown","action":"","parameters":{},"confidence":0.0}
"""
        print("LLMClassifier is ready.")

    def classify(self, transcript: str) -> dict:
        """Uses the LLM to classify the transcript."""
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': transcript}
                ],
                options={'temperature': 0.0}  # We want deterministic output
            )
            json_string = response['message']['content']
            json_string = json_string.strip().replace("```json", "").replace("```", "")
            result = json.loads(json_string)
            result["transcript"] = transcript
            return result

        except Exception as e:
            print(f"[LLMClassifier] ERROR: Failed to parse LLM response: {e}")
            return {"type": "unknown", "confidence": 0.0, "transcript": transcript}
