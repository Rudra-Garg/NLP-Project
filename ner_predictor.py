from pathlib import Path

import joblib
import spacy

# Import the feature engineering functions from our existing script
from ner_feature_engineering import word2features


class NERPredictor:
    """
    A class to load the trained CRF model and make predictions on new text.
    """

    def __init__(self, model_path: Path):
        print("Initializing NER Predictor...")
        if not model_path.exists():
            raise FileNotFoundError(f"NER model not found at: {model_path}")

        # Load the trained CRF model from the file
        self.model = joblib.load(model_path)
        print("NER model loaded successfully.")

        # Load the spaCy model for feature extraction
        self.nlp = spacy.load("en_core_web_sm")
        print("NER Predictor is ready.")

    def _extract_entities_from_tags(self, tokens, tags):
        """
        Parses a list of IOB tags and corresponding tokens to extract named entities.
        """
        entities = {}
        current_entity_tokens = []
        current_entity_type = None

        for token, tag in zip(tokens, tags):
            if tag.startswith('B-'):
                # If we have a pending entity, save it first
                if current_entity_type:
                    entity_name = " ".join(current_entity_tokens)
                    entities[current_entity_type] = entity_name

                # Start a new entity
                current_entity_type = tag[2:]  # Get the type (e.g., APP_NAME)
                current_entity_tokens = [token]

            elif tag.startswith('I-') and current_entity_type == tag[2:]:
                # Continue the current entity
                current_entity_tokens.append(token)

            else:  # Tag is 'O' or a B- tag for a new entity
                # If we have a pending entity, save it
                if current_entity_type:
                    entity_name = " ".join(current_entity_tokens)
                    entities[current_entity_type] = entity_name

                # Reset
                current_entity_tokens = []
                current_entity_type = None

        # Save any leftover entity at the end of the sentence
        if current_entity_type:
            entity_name = " ".join(current_entity_tokens)
            entities[current_entity_type] = entity_name

        return entities

    def predict(self, transcript: str):
        """
        Predicts entities in a given transcript.
        """
        if not transcript:
            return {}

        # Use spaCy to tokenize the text
        doc = self.nlp(transcript)
        tokens = [token.text for token in doc]

        # 1. Convert the new transcript into features
        features = [word2features(doc, i) for i in range(len(doc))]

        # 2. Use the trained model to predict IOB tags
        #    Note: crf.predict() expects a list of sequences, so we wrap our features in a list
        predicted_tags = self.model.predict([features])[0]

        # 3. Parse the tags to extract entities
        entities = self._extract_entities_from_tags(tokens, predicted_tags)

        return entities


# This block allows you to test the predictor independently
if __name__ == '__main__':
    model_file_path = Path(__file__).parent / "models" / "ner" / "ner_model.joblib"
    predictor = NERPredictor(model_file_path)

    test_transcripts = [
        "can you launch google chrome for me",
        "please calculate what is 25 times ( 4 plus 3 )",
        "open the task manager",
        "what time is it",
        "calculate the square root of 81"
    ]

    for text in test_transcripts:
        entities = predictor.predict(text)
        print(f'Transcript: "{text}"')
        print(f'  -> Entities: {entities}\n')
