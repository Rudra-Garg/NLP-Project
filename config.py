import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_settings():
    """
    Loads settings from config.yaml and merges secrets from .env.
    
    This provides a single, unified configuration object for the entire application.
    """
    # Load the main configuration file
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r') as f:
        settings = yaml.safe_load(f)

    # Load environment variables from .env file for secrets
    load_dotenv()

    # --- Merge Secrets into the Settings Dictionary ---
    # This keeps all configuration, including secrets, accessible from one object,
    # while keeping the secrets themselves out of the version-controlled config.yaml.

    picovoice_key = os.getenv("ACCESS_KEY")
    if picovoice_key:
        settings['picovoice']['access_key'] = picovoice_key
    else:
        # Handle case where key is missing but don't crash immediately.
        # The worker will handle the error.
        settings['picovoice']['access_key'] = None

    return settings


# Create a single settings object to be imported by other modules
settings = load_settings()
