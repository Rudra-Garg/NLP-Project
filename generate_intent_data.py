import json
import random
from pathlib import Path


def generate_examples():
    """
    Loads intent templates and generates a large, diverse set of example
    utterances for training the embedding classifier.
    """
    print("--- Generating Expanded Intent Training Data ---")
    project_root = Path(__file__).parent
    intents_path = project_root / "data" / "intents.json"

    with open(intents_path, 'r') as f:
        intents_data = json.load(f)

    # Define a rich dictionary of placeholder values
    placeholder_values = {
        "app_name": [
            "notepad", "calculator", "chrome", "firefox", "word", "excel", "vscode",
            "visual studio", "photoshop", "spotify", "task manager", "control panel",
            "gimp", "blender", "steam", "discord", "slack", "zoom", "File Explorer",
            "Terminal", "System Preferences", "Activity Monitor"
        ],
        "expression": [
            "2 plus 2", "100 divided by 5", "the square root of 144", "5 times 8",
            "(10 + 5) * 3", "2 to the power of 8", "50 percent of 200", "19 minus 7",
            "what is 3 factorial", "sine of 90 degrees", "log of 100"
        ],
        "level": [str(i) for i in range(0, 101, 10)] + [f"{i} percent" for i in range(10, 100, 20)]
    }

    # Add conversational noise to make the data more realistic
    prefixes = ["", "please", "can you", "could you", "hey loki", "alright", "okay"]
    suffixes = ["", "for me", "please", "now", "if you could"]

    all_examples = []
    for intent_group in intents_data:
        intent_type = intent_group["type"]
        action = intent_group["action"]

        for template in intent_group["prompts"]:
            placeholders = re.findall(r'\{(.*?)\}', template)

            if not placeholders:
                # For templates without placeholders, just add variations with noise
                for _ in range(5):  # Create a few variations for each
                    text = f"{random.choice(prefixes)} {template} {random.choice(suffixes)}".strip()
                    all_examples.append({"text": text, "type": intent_type, "action": action})
            else:
                # For templates with placeholders, generate examples
                param_name = placeholders[0]
                if param_name in placeholder_values:
                    # Use a sample to avoid creating a gigantic file, but ensure diversity
                    sample_values = random.sample(placeholder_values[param_name],
                                                  min(len(placeholder_values[param_name]), 5))
                    for value in sample_values:
                        text = template.replace(f"{{{param_name}}}", value)
                        # Add noise to a subset of these too
                        if random.random() < 0.7:
                            text = f"{random.choice(prefixes)} {text} {random.choice(suffixes)}".strip()
                        all_examples.append({"text": text, "type": intent_type, "action": action})

    # Ensure all original prompts are also in the list
    for intent_group in intents_data:
        for template in intent_group["prompts"]:
            if not any(p in template for p in ["{", "}"]):
                all_examples.append({"text": template, "type": intent_group["type"], "action": intent_group["action"]})

    print(f"Generated a total of {len(all_examples)} example sentences.")
    random.shuffle(all_examples)

    # Save to the file that the FastClassifier will use for training
    output_path = project_root / "data" / "intent_training_data.json"
    with open(output_path, 'w') as f:
        json.dump(all_examples, f, indent=2)

    print(f"Expanded intent data saved to {output_path}")


if __name__ == "__main__":
    import re

    generate_examples()
