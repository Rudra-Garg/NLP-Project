import json
import random
from pathlib import Path


def generate_app_launch_examples():
    """
    Generate diverse examples for launching applications.
    Covers various phrasings and common applications for Windows and Mac.
    Includes developer tools and professional applications.
    """
    # Single-word applications
    apps = [
        # Windows built-in
        "notepad", "calculator", "paint", "wordpad", "snipping",
        "cmd", "powershell", "regedit", "msconfig", "taskmanager",

        # Browsers
        "chrome", "firefox", "edge", "brave", "opera", "safari",

        # Microsoft Office
        "word", "excel", "powerpoint", "outlook", "onenote", "access", "publisher",

        # Media & Entertainment
        "spotify", "vlc", "itunes", "audacity", "obs", "discord", "telegram",
        "whatsapp", "skype", "zoom", "slack", "teams",

        # Developer Tools (single word)
        "vscode", "pycharm", "webstorm", "intellij", "eclipse", "netbeans",
        "sublime", "atom", "notepad++", "vim", "emacs", "git", "docker",
        "postman", "insomnia", "xampp", "wamp", "putty", "wireshark",

        # Design & Creative
        "photoshop", "illustrator", "premiere", "aftereffects", "lightroom",
        "figma", "sketch", "gimp", "blender", "inkscape",

        # Utilities
        "winrar", "7zip", "ccleaner", "malwarebytes", "steam", "epic",
        "dropbox", "onedrive", "googledrive", "evernote", "notion",
        "filezilla", "thunderbird", "calibre"
    ]

    # Multi-word applications (Windows & Mac)
    multi_word_apps = [
        # Windows System
        ["task", "manager"], ["control", "panel"], ["file", "explorer"],
        ["windows", "terminal"], ["windows", "defender"], ["device", "manager"],
        ["disk", "cleanup"], ["system", "configuration"], ["event", "viewer"],
        ["registry", "editor"], ["resource", "monitor"], ["performance", "monitor"],
        ["windows", "media", "player"], ["snipping", "tool"], ["sticky", "notes"],
        ["remote", "desktop"], ["task", "scheduler"],

        # Browsers
        ["google", "chrome"], ["mozilla", "firefox"], ["microsoft", "edge"],
        ["internet", "explorer"], ["brave", "browser"],

        # Microsoft Office
        ["microsoft", "word"], ["microsoft", "excel"], ["microsoft", "powerpoint"],
        ["microsoft", "outlook"], ["microsoft", "teams"], ["microsoft", "onenote"],
        ["microsoft", "access"], ["microsoft", "publisher"],

        # Developer Tools
        ["visual", "studio"], ["visual", "studio", "code"], ["android", "studio"],
        ["sql", "server"], ["mysql", "workbench"], ["mongodb", "compass"],
        ["github", "desktop"], ["git", "bash"], ["node", "js"], ["sql", "developer"],
        ["intellij", "idea"], ["pycharm", "professional"], ["webstorm", "ide"],
        ["sublime", "text"], ["notepad", "plus", "plus"], ["brackets", "editor"],
        ["jupyter", "notebook"], ["anaconda", "navigator"], ["docker", "desktop"],
        ["virtual", "box"], ["vmware", "workstation"], ["hyper", "v"],

        # Adobe Suite
        ["adobe", "photoshop"], ["adobe", "illustrator"], ["adobe", "premiere"],
        ["adobe", "after", "effects"], ["adobe", "xd"], ["adobe", "lightroom"],
        ["adobe", "acrobat"], ["adobe", "reader"],

        # Communication
        ["microsoft", "teams"], ["zoom", "meetings"], ["google", "meet"],
        ["cisco", "webex"], ["slack", "app"],

        # Mac Specific
        ["app", "store"], ["system", "preferences"], ["activity", "monitor"],
        ["disk", "utility"], ["terminal", "app"], ["safari", "browser"],
        ["text", "edit"], ["preview", "app"], ["font", "book"],
        ["time", "machine"], ["finder", "app"],

        # Other Popular
        ["obs", "studio"], ["epic", "games"], ["steam", "client"],
        ["battle", "net"], ["league", "of", "legends"], ["google", "drive"],
        ["one", "drive"]
    ]

    launch_phrases = [
        "open", "launch", "start", "run", "open up",
        "can you open", "please open", "i want to open",
        "start up", "fire up", "bring up", "execute",
        "could you launch", "please launch", "i need to open",
        "show me", "pull up", "bring up", "load",
        "could you start", "i want to start", "i need to start"
    ]

    examples = []

    # Single word apps - generate more examples
    for app in apps:
        for phrase in launch_phrases[:8]:  # Use more phrases
            tokens = phrase.split() + [app]
            tags = ['O'] * len(phrase.split()) + ['B-APP_NAME']
            examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    # Multi-word apps - generate more examples
    for app_tokens in multi_word_apps:
        for phrase in launch_phrases[:6]:
            tokens = phrase.split() + app_tokens
            tags = ['O'] * len(phrase.split())
            tags.extend(['B-APP_NAME'] + ['I-APP_NAME'] * (len(app_tokens) - 1))
            examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    # Add variations with articles and descriptors
    descriptors = ["the", "my", "the latest"]
    for app in apps[:30]:
        for desc in descriptors:
            tokens = ["open"] + desc.split() + [app]
            tags = ['O'] * (1 + len(desc.split())) + ['B-APP_NAME']
            examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    # Add "application" and "program" suffix variations
    for app in apps[:20]:
        # "open chrome application"
        tokens = ["open", app, "application"]
        tags = ['O', 'B-APP_NAME', 'O']
        examples.append([[token, tag] for token, tag in zip(tokens, tags)])

        # "launch notepad program"
        tokens = ["launch", app, "program"]
        tags = ['O', 'B-APP_NAME', 'O']
        examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    # Windows-specific variations with .exe
    windows_apps = ["notepad", "calc", "mspaint", "cmd", "powershell", "regedit"]
    for app in windows_apps:
        # "run notepad.exe"
        tokens = ["run", app + ".exe"]
        tags = ['O', 'B-APP_NAME']
        examples.append([[token, tag] for token, tag in zip(tokens, tags)])

        # "execute cmd.exe"
        tokens = ["execute", app + ".exe"]
        tags = ['O', 'B-APP_NAME']
        examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    # Developer-specific phrases
    dev_phrases = [
        (["open", "vscode", "in", "this", "folder"],
         ['O', 'B-APP_NAME', 'O', 'O', 'O']),
        (["launch", "visual", "studio", "code", "here"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'I-APP_NAME', 'O']),
        (["start", "docker", "desktop"],
         ['O', 'B-APP_NAME', 'I-APP_NAME']),
        (["open", "android", "studio", "project"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),
        (["launch", "sql", "server", "management", "studio"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'I-APP_NAME', 'I-APP_NAME']),
        (["open", "git", "bash", "terminal"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),
        (["start", "jupyter", "notebook", "server"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),
        (["run", "mongodb", "compass"],
         ['O', 'B-APP_NAME', 'I-APP_NAME']),
        (["open", "mysql", "workbench"],
         ['O', 'B-APP_NAME', 'I-APP_NAME']),
        (["launch", "postman", "api", "client"],
         ['O', 'B-APP_NAME', 'O', 'O']),
    ]

    examples.extend([[token, tag] for token, tag in zip(tokens, tags)]
                    for tokens, tags in dev_phrases)

    # Add conversational variations with more apps
    conversational = [
        # Windows System Apps
        (["hey", "can", "you", "launch", "task", "manager"],
         ['O', 'O', 'O', 'O', 'B-APP_NAME', 'I-APP_NAME']),
        (["i", "need", "to", "open", "control", "panel"],
         ['O', 'O', 'O', 'O', 'B-APP_NAME', 'I-APP_NAME']),
        (["please", "start", "file", "explorer"],
         ['O', 'O', 'B-APP_NAME', 'I-APP_NAME']),
        (["could", "you", "open", "the", "registry", "editor"],
         ['O', 'O', 'O', 'O', 'B-APP_NAME', 'I-APP_NAME']),
        (["open", "windows", "terminal", "please"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),

        # Browsers
        (["i", "want", "to", "browse", "the", "web", "with", "chrome"],
         ['O', 'O', 'O', 'O', 'O', 'O', 'O', 'B-APP_NAME']),
        (["can", "you", "open", "firefox", "for", "me"],
         ['O', 'O', 'O', 'B-APP_NAME', 'O', 'O']),
        (["launch", "microsoft", "edge", "browser"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),

        # Office Apps
        (["i", "need", "word", "to", "write", "a", "document"],
         ['O', 'O', 'B-APP_NAME', 'O', 'O', 'O', 'O']),
        (["open", "excel", "to", "create", "a", "spreadsheet"],
         ['O', 'B-APP_NAME', 'O', 'O', 'O', 'O']),
        (["start", "powerpoint", "for", "my", "presentation"],
         ['O', 'B-APP_NAME', 'O', 'O', 'O']),
        (["can", "you", "launch", "outlook", "to", "check", "email"],
         ['O', 'O', 'O', 'B-APP_NAME', 'O', 'O', 'O']),

        # Developer Tools
        (["hey", "open", "vscode", "for", "coding"],
         ['O', 'O', 'B-APP_NAME', 'O', 'O']),
        (["i", "need", "pycharm", "to", "write", "python"],
         ['O', 'O', 'B-APP_NAME', 'O', 'O', 'O']),
        (["launch", "visual", "studio", "please"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),
        (["start", "android", "studio", "for", "development"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O', 'O']),
        (["open", "sublime", "text", "editor"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O']),
        (["i", "want", "to", "use", "docker", "desktop"],
         ['O', 'O', 'O', 'O', 'B-APP_NAME', 'I-APP_NAME']),
        (["can", "you", "start", "git", "bash"],
         ['O', 'O', 'O', 'B-APP_NAME', 'I-APP_NAME']),
        (["launch", "postman", "for", "api", "testing"],
         ['O', 'B-APP_NAME', 'O', 'O', 'O']),

        # Creative Apps
        (["open", "photoshop", "to", "edit", "photos"],
         ['O', 'B-APP_NAME', 'O', 'O', 'O']),
        (["i", "need", "adobe", "premiere", "for", "video", "editing"],
         ['O', 'O', 'B-APP_NAME', 'I-APP_NAME', 'O', 'O', 'O']),
        (["launch", "obs", "studio", "to", "stream"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O', 'O']),
        (["start", "blender", "for", "3d", "modeling"],
         ['O', 'B-APP_NAME', 'O', 'O', 'O']),

        # Communication Apps
        (["open", "discord", "to", "chat"],
         ['O', 'B-APP_NAME', 'O', 'O']),
        (["launch", "microsoft", "teams", "for", "meeting"],
         ['O', 'B-APP_NAME', 'I-APP_NAME', 'O', 'O']),
        (["start", "zoom", "for", "conference"],
         ['O', 'B-APP_NAME', 'O', 'O']),
        (["i", "want", "to", "use", "slack"],
         ['O', 'O', 'O', 'O', 'B-APP_NAME']),
    ]

    for tokens, tags in conversational:
        examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    return examples


def generate_math_examples():
    """
    Generate diverse mathematical expression examples.
    Covers various operations and phrasings.
    """
    examples = []

    # Simple arithmetic with different phrasings
    operations = [
        ("plus", "+"), ("minus", "-"), ("times", "×"),
        ("divided by", "÷"), ("multiplied by", "×")
    ]

    question_starters = [
        ["what", "is"],
        ["calculate"],
        ["compute"],
        ["solve"],
        ["tell", "me"],
        ["what's"],
        ["find"]
    ]

    # Generate simple arithmetic: "what is X op Y"
    for _ in range(30):
        num1 = random.randint(1, 100)
        num2 = random.randint(1, 100)
        op_word, _ = random.choice(operations)
        starter = random.choice(question_starters)

        tokens = starter + [str(num1)] + op_word.split() + [str(num2)]
        tags = ['O'] * len(starter)
        tags.extend(['B-MATH_EXPRESSION'] + ['I-MATH_EXPRESSION'] * (len(op_word.split()) + 1))

        examples.append([[token, tag] for token, tag in zip(tokens, tags)])

    # Complex expressions with parentheses
    complex_examples = [
        (["what", "is", "(", "5", "plus", "3", ")", "times", "2"],
         ['O', 'O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["calculate", "2", "times", "(", "10", "minus", "4", ")"],
         ['O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["solve", "(", "15", "divided", "by", "3", ")", "plus", "7"],
         ['O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),
    ]

    examples.extend([[token, tag] for token, tag in zip(tokens, tags)]
                    for tokens, tags in complex_examples)

    # Special functions
    special_functions = [
        (["square", "root", "of", "144"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["cube", "root", "of", "27"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["5", "squared"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["2", "to", "the", "power", "of", "8"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["factorial", "of", "5"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["sine", "of", "45", "degrees"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["cosine", "of", "90"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["log", "of", "100"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),
    ]

    for tokens, tags in special_functions:
        for starter in question_starters[:4]:
            full_tokens = starter + tokens
            full_tags = ['O'] * len(starter) + tags
            examples.append([[token, tag] for token, tag in zip(full_tokens, full_tags)])

    # Percentage calculations
    percentage_examples = [
        (["what", "is", "20", "percent", "of", "50"],
         ['O', 'O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["calculate", "15", "%", "of", "200"],
         ['O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["find", "25", "percent", "of", "80"],
         ['O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),
    ]

    examples.extend([[token, tag] for token, tag in zip(tokens, tags)]
                    for tokens, tags in percentage_examples)

    # Multi-step expressions
    multi_step = [
        (["add", "5", "and", "10", "then", "multiply", "by", "2"],
         ['B-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["what", "is", "the", "sum", "of", "7", "and", "13"],
         ['O', 'O', 'O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),

        (["find", "the", "difference", "between", "100", "and", "37"],
         ['O', 'O', 'B-MATH_EXPRESSION', 'I-MATH_EXPRESSION',
          'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION', 'I-MATH_EXPRESSION']),
    ]

    examples.extend([[token, tag] for token, tag in zip(tokens, tags)]
                    for tokens, tags in multi_step)

    return examples


def generate_negative_examples():
    """
    Generate examples with no entities to help the model learn 'O' tags.
    These are important for reducing false positives.
    """
    negative_sentences = [
        ["what", "time", "is", "it"],
        ["tell", "me", "a", "joke"],
        ["what's", "the", "weather", "like"],
        ["how", "are", "you", "doing"],
        ["thank", "you"],
        ["goodbye"],
        ["hello"],
        ["can", "you", "help", "me"],
        ["what", "can", "you", "do"],
        ["i", "need", "assistance"],
        ["show", "me", "the", "menu"],
        ["go", "back"],
        ["cancel", "that"],
        ["never", "mind"],
        ["repeat", "that"],
        ["what", "did", "you", "say"],
    ]

    return [[[token, 'O'] for token in sentence] for sentence in negative_sentences]


def create_ner_training_data():
    """
    Main function to generate comprehensive NER training data.
    """
    print("Generating NER training data...")

    # Generate examples for each entity type
    app_examples = generate_app_launch_examples()
    print(f"Generated {len(app_examples)} APP_NAME examples")

    math_examples = generate_math_examples()
    print(f"Generated {len(math_examples)} MATH_EXPRESSION examples")

    negative_examples = generate_negative_examples()
    print(f"Generated {len(negative_examples)} negative examples (no entities)")

    # Combine all examples
    all_examples = app_examples + math_examples + negative_examples

    # Shuffle to mix different entity types
    random.shuffle(all_examples)

    print(f"\nTotal training examples: {len(all_examples)}")

    # Calculate statistics
    entity_counts = {'APP_NAME': 0, 'MATH_EXPRESSION': 0, 'O_only': 0}
    for example in all_examples:
        has_entity = False
        for token, tag in example:
            if tag.startswith('B-APP_NAME'):
                entity_counts['APP_NAME'] += 1
                has_entity = True
            elif tag.startswith('B-MATH_EXPRESSION'):
                entity_counts['MATH_EXPRESSION'] += 1
                has_entity = True
        if not has_entity:
            entity_counts['O_only'] += 1

    print(f"\nDataset statistics:")
    print(f"  Examples with APP_NAME: {entity_counts['APP_NAME']}")
    print(f"  Examples with MATH_EXPRESSION: {entity_counts['MATH_EXPRESSION']}")
    print(f"  Examples with no entities: {entity_counts['O_only']}")

    # Save to file
    project_root = Path(__file__).parent
    output_path = project_root / "data" / "ner_training_data.json"
    output_path.parent.mkdir(exist_ok=True)

    print(f"\nSaving to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_examples, f, indent=2, ensure_ascii=False)

    print("✓ NER training data created successfully!")

    # Save a small sample for inspection
    sample_path = project_root / "data" / "ner_sample.json"
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(all_examples[:20], f, indent=2, ensure_ascii=False)
    print(f"✓ Sample saved to {sample_path} for inspection")

    return all_examples


if __name__ == "__main__":
    create_ner_training_data()
