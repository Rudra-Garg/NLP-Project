import spacy
from spacy.tokens import Doc

# Load the spaCy model once for efficiency
nlp = spacy.load("en_core_web_sm")


def get_word_shape(word):
    """
    Generates a 'word shape' feature.
    This helps the model generalize from specific words to patterns.
    E.g., "Google" -> "Xxxxx", "2+2" -> "d+d", "VSCode" -> "XXxxxx"
    """
    shape = ""
    for char in word:
        if char.isupper():
            shape += "X"
        elif char.islower():
            shape += "x"
        elif char.isdigit():
            shape += "d"
        else:
            shape += char
    return shape


def word2features(doc, i):
    """
    Extracts a dictionary of features for a single word in a spaCy Doc.
    This is the core of our feature engineering.
    """
    word = doc[i]

    # Base features for the current word
    features = {
        'bias': 1.0,
        'word.lower()': word.lower_,
        'word.shape': get_word_shape(word.text),
        'word.isupper()': word.is_upper,
        'word.istitle()': word.is_title,
        'word.isdigit()': word.is_digit,
        'pos_tag': word.pos_,  # Coarse-grained POS tag (e.g., VERB, NOUN)
        'fine_tag': word.tag_,  # Fine-grained POS tag (e.g., VBG, NNP)
    }

    # Features for the PREVIOUS word (context)
    if i > 0:
        prev_word = doc[i - 1]
        features.update({
            '-1:word.lower()': prev_word.lower_,
            '-1:word.istitle()': prev_word.is_title,
            '-1:word.isupper()': prev_word.is_upper,
            '-1:pos_tag': prev_word.pos_,
            '-1:fine_tag': prev_word.tag_,
        })
    else:
        # Indicate that this is the beginning of a sentence
        features['BOS'] = True

    # Features for the NEXT word (context)
    if i < len(doc) - 1:
        next_word = doc[i + 1]
        features.update({
            '+1:word.lower()': next_word.lower_,
            '+1:word.istitle()': next_word.is_title,
            '+1:word.isupper()': next_word.is_upper,
            '+1:pos_tag': next_word.pos_,
            '+1:fine_tag': next_word.tag_,
        })
    else:
        # Indicate that this is the end of a sentence
        features['EOS'] = True

    return features


# Helper functions to process the entire dataset
def sent2tokens(sent):
    return [token for token, tag in sent]


def sent2labels(sent):
    return [tag for token, tag in sent]


def sent2features(sent):
    """
    Converts a sentence (list of [word, tag]) into a list of feature dicts.

    --- THIS IS THE CORRECTED PART ---
    Instead of joining and re-tokenizing, we create a Doc object directly
    from the pre-tokenized words to ensure our tokens and labels always match.
    """
    tokens = sent2tokens(sent)

    # 1. Create a spaCy Doc from our list of tokens
    doc = Doc(nlp.vocab, words=tokens)

    # 2. Process the doc with the components of the pipeline (e.g., tagger, parser).
    #    This adds the linguistic annotations (like POS tags) without changing tokenization.
    for name, proc in nlp.pipeline:
        doc = proc(doc)

    return [word2features(doc, i) for i in range(len(doc))]


# This block allows you to test the feature extraction on a sample sentence
if __name__ == "__main__":
    import json
    from pathlib import Path
    import pprint

    # Load the data we generated in Phase 1
    data_path = Path(__file__).parent / "data" / "ner_training_data.json"
    with open(data_path, 'r') as f:
        training_data = json.load(f)

    print(f"Loaded {len(training_data)} sentences.")

    # Find a potentially problematic sentence to test
    sample_sentence = [['run', 'O'], ['notepad.exe', 'B-APP_NAME']]
    print("\nOriginal Sentence (with labels):")
    print(sample_sentence)

    # Convert it to features
    features = sent2features(sample_sentence)
    print("\nFeatures for the second word '{}':".format(sample_sentence[1][0]))
    pprint.pprint(features[1])

    # Verify lengths
    print(f"\nVerification:")
    print(f"  Number of tokens: {len(sent2tokens(sample_sentence))}")
    print(f"  Number of labels: {len(sent2labels(sample_sentence))}")
    print(f"  Number of feature dicts: {len(features)}")

    if len(sent2tokens(sample_sentence)) == len(features):
        print("✓ Lengths match!")
    else:
        print("✗ Lengths DO NOT match!")
