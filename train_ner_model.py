import json
from pathlib import Path

import joblib
import sklearn_crfsuite
from sklearn.model_selection import train_test_split
from sklearn_crfsuite import metrics

# Import the feature engineering functions from our previous script
from ner_feature_engineering import sent2features, sent2labels


def train_ner_model():
    """
    Loads data, trains the CRF model, evaluates it, and saves the final model.
    """
    print("--- Phase 3: NER Model Training ---")

    # 1. Load the data prepared in Phase 1
    project_root = Path(__file__).parent
    data_path = project_root / "data" / "ner_training_data.json"
    print(f"Loading training data from {data_path}...")
    with open(data_path, 'r') as f:
        training_data = json.load(f)
    print(f"Loaded {len(training_data)} sentences.")

    # 2. Convert sentences into features and labels using our functions from Phase 2
    print("Extracting features and labels from the dataset...")
    X = [sent2features(s) for s in training_data]
    y = [sent2labels(s) for s in training_data]
    print("Feature extraction complete.")

    # 3. Split the data into training and testing sets (80/20 split)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nData split:")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Testing samples:  {len(X_test)}")

    # 4. Initialize and train the CRF model
    print("\nInitializing CRF model...")
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',  # L-BFGS is a standard and effective optimization algorithm
        c1=0.1,  # Regularization parameter
        c2=0.1,  # Regularization parameter
        max_iterations=100,  # Number of training iterations
        all_possible_transitions=True  # Allows the model to learn more complex transition patterns
    )

    print("Training the model... (This may take a moment)")
    crf.fit(X_train, y_train)
    print("Model training complete.")

    # 5. Save the trained model to the models directory
    model_dir = project_root / "models" / "ner"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "ner_model.joblib"

    print(f"\nSaving model to: {model_path}")
    joblib.dump(crf, model_path)
    print("Model saved successfully.")

    # 6. Evaluate the model on the test set
    print("\n--- Model Evaluation on Test Set ---")
    y_pred = crf.predict(X_test)

    # Get a list of all labels (entity types) in the dataset, excluding 'O'
    labels = list(crf.classes_)
    labels.remove('O')

    f1_score = metrics.flat_f1_score(y_test, y_pred, average='weighted', labels=labels)
    print(f"Weighted F1 Score (excluding 'O'): {f1_score:.4f}")

    # Print a detailed classification report
    report = metrics.flat_classification_report(
        y_test, y_pred, labels=labels, digits=4
    )
    print("\nClassification Report:")
    print(report)


if __name__ == "__main__":
    train_ner_model()
