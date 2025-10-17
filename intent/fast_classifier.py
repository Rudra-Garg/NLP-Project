import json
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class FastClassifier:
    """
    A fast, embedding-based intent classifier. It works by pre-computing
    embeddings for known command prompts and finding the closest match for
    a new user transcript using cosine similarity.
    """
    SIMILARITY_THRESHOLD = 0.75  # Confidence threshold for a match

    def __init__(self, intents_path: Path):
        print("Initializing FastClassifier...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        self._load_and_embed_intents(intents_path)
        print("FastClassifier is ready.")

    def _load_and_embed_intents(self, intents_path: Path):
        """Loads intents from JSON and pre-computes their embeddings."""
        print(f"Loading intents from '{intents_path}'...")
        with open(intents_path, 'r') as f:
            intents_data = json.load(f)

        self.known_intents = []
        prompts_to_embed = []

        for intent_group in intents_data:
            for prompt in intent_group["prompts"]:
                self.known_intents.append({
                    "text": prompt,
                    "type": intent_group["type"],
                    "action": intent_group["action"]
                })
                prompts_to_embed.append(prompt)

        print(f"Pre-computing embeddings for {len(prompts_to_embed)} known prompts...")
        self.known_embeddings = self.model.encode(prompts_to_embed)
        print("Embeddings computed successfully.")

    def classify(self, transcript: str) -> dict:
        """Classifies the transcript and extracts parameters."""
        if not transcript:
            return {"type": "unknown", "confidence": 0.0, "transcript": ""}

        # 1. Find the best matching intent via cosine similarity
        transcript_embedding = self.model.encode([transcript])
        similarities = cosine_similarity(transcript_embedding, self.known_embeddings)[0]
        best_match_index = similarities.argmax()
        confidence = similarities[best_match_index]

        if confidence < self.SIMILARITY_THRESHOLD:
            return {"type": "unknown", "confidence": float(confidence), "transcript": transcript}

        best_match = self.known_intents[best_match_index]
        intent = {
            "type": best_match["type"],
            "action": best_match["action"],
            "confidence": float(confidence),
            "parameters": {},
            "transcript": transcript
        }

        # 2. Parameter Extraction (simple for now)
        if intent["type"] == "calculation":
            # Extract the part of the string that is the math expression
            # This regex looks for numbers, operators, and parentheses
            match = re.search(r'calculate|what is|compute|evaluate|how much is', transcript, re.IGNORECASE)
            if match:
                expression = transcript[match.end():].strip()
                # A simple validation to avoid empty expressions
                if re.search(r'[\d()+\-*/.^]', expression):
                    intent["parameters"]["expression"] = expression

        return intent
