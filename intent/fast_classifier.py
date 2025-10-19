import json
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer, util


class FastClassifier:
    """
    A fast, embedding-based intent classifier that uses prompt templates for
    robust parameter extraction.
    """

    def __init__(self, intents_path: Path, model_name: str, threshold: float):
        print("Initializing FastClassifier...")
        self.SIMILARITY_THRESHOLD = threshold

        print(f"Loading SentenceTransformer model: '{model_name}'...")
        self.model = SentenceTransformer(model_name, device='cpu')

        self._load_and_embed_intents(intents_path)
        print("FastClassifier is ready.")

    def _extract_template_info(self, prompt: str):
        params = re.findall(r'\{(.*?)\}', prompt)
        clean_prompt = re.sub(r'\{.*?\}', '', prompt).strip()
        return clean_prompt, params

    def _load_and_embed_intents(self, intents_path: Path):
        print(f"Loading and processing intents from '{intents_path}'...")
        with open(intents_path, 'r') as f:
            intents_data = json.load(f)

        self.known_intents = []
        prompts_to_embed = []

        for intent_group in intents_data:
            for prompt_template in intent_group["prompts"]:
                clean_prompt, params = self._extract_template_info(prompt_template)

                self.known_intents.append({
                    "template": prompt_template,
                    "clean_prompt": clean_prompt,
                    "type": intent_group["type"],
                    "action": intent_group["action"],
                    "params": params
                })
                prompts_to_embed.append(clean_prompt)

        print(f"Pre-computing embeddings for {len(prompts_to_embed)} known prompt templates...")
        self.known_embeddings = self.model.encode(prompts_to_embed)
        print("Embeddings computed successfully.")

    def _extract_parameters(self, transcript: str, best_match: dict) -> dict:
        parameters = {}
        template = best_match['template']

        for param_name in best_match['params']:
            placeholder = f"{{{param_name}}}"
            parts = template.split(placeholder)
            prefix = parts[0]
            suffix = parts[1] if len(parts) > 1 else ""

            start_index = len(prefix) if transcript.lower().startswith(prefix) else -1

            # Handle suffix if it exists
            if suffix:
                end_index = transcript.lower().rfind(suffix)
                if end_index == -1:  # Suffix not found, something is wrong
                    continue
            else:
                end_index = len(transcript)

            if start_index != -1 and end_index >= start_index:
                value = transcript[start_index:end_index].strip()
                if value:
                    parameters[param_name] = value

        return parameters

    def classify(self, transcript: str) -> dict:
        if not transcript:
            return {"type": "unknown", "confidence": 0.0, "transcript": ""}

        transcript_embedding = self.model.encode(transcript.lower())

        scores = util.dot_score(transcript_embedding, self.known_embeddings)[0]

        best_match_index = scores.argmax()
        confidence = scores[best_match_index].item()

        # Simple normalization based on expected score range for this model
        normalized_confidence = min(max(confidence / 30, 0.0), 1.0)

        if normalized_confidence < self.SIMILARITY_THRESHOLD:
            return {"type": "unknown", "confidence": normalized_confidence, "transcript": transcript}

        best_match = self.known_intents[best_match_index]

        if best_match["type"] == "unknown":
            return {"type": "unknown", "confidence": 1.0 - normalized_confidence, "transcript": transcript}

        intent = {
            "type": best_match["type"],
            "action": best_match["action"],
            "confidence": normalized_confidence,
            "parameters": {},
            "transcript": transcript
        }

        if best_match['params']:
            intent["parameters"] = self._extract_parameters(transcript, best_match)

        return intent
