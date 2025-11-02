import json
from pathlib import Path
import spacy
from sentence_transformers import SentenceTransformer, util


class FastClassifier:
    def __init__(self, intents_path: Path, model_name: str, threshold: float):
        print("Initializing FastClassifier...")
        self.SIMILARITY_THRESHOLD = threshold
        print(f"Loading SentenceTransformer model: '{model_name}'...")
        self.model = SentenceTransformer(model_name, device='cpu')
        print("Loading spaCy model for lemmatization...")
        self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
        self._load_and_embed_intents(intents_path)
        print("FastClassifier is ready.")

    def _load_and_embed_intents(self, intents_path: Path):
        print(f"Loading generated intent examples from '{intents_path}'...")
        with open(intents_path, 'r') as f:
            intent_examples = json.load(f)

        self.known_intents = intent_examples
        prompts_to_embed = [example["text"] for example in self.known_intents]

        print(f"Pre-computing embeddings for {len(prompts_to_embed)} known example prompts...")
        self.known_embeddings = self.model.encode(prompts_to_embed, convert_to_tensor=True)
        print("Embeddings computed successfully.")

    def classify(self, transcript: str) -> dict:
        if not transcript:
            return {"type": "unknown", "confidence": 0.0, "transcript": ""}

        doc = self.nlp(transcript.lower())
        lemmatized_transcript = " ".join([token.lemma_ for token in doc])
        print(f"[FastClassifier] Original: '{transcript}' -> Lemmatized: '{lemmatized_transcript}'")

        transcript_embedding = self.model.encode(lemmatized_transcript, convert_to_tensor=True)
        scores = util.cos_sim(transcript_embedding, self.known_embeddings)[0]

        best_match_index = scores.argmax()
        confidence = scores[best_match_index].item()

        if confidence < self.SIMILARITY_THRESHOLD:
            return {"type": "unknown", "confidence": confidence, "transcript": transcript}

        best_match = self.known_intents[best_match_index]

        if best_match["type"] == "unknown":
            return {"type": "unknown", "confidence": 1.0 - confidence, "transcript": transcript}

        # The NER model is now the primary source for parameters.
        # This classifier's only job is to provide the type and action.
        return {
            "type": best_match["type"],
            "action": best_match["action"],
            "confidence": confidence,
            "parameters": {},
            "transcript": transcript
        }
