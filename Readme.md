# LOKI - Python Voice Assistant

This repository is the Python port of the LOKI C++ Voice Assistant. It leverages a modern stack of local-first AI tools to provide a private, responsive, and powerful voice interaction experience. The assistant runs entirely on your local machine, ensuring your data remains yours.

The core architecture is designed for speed and accuracy, featuring a dual-layer intent classification system that handles common commands instantly and falls back to a local Large Language Model (LLM) for more complex queries.

## Core Features (Implemented)

This Python version has a robust foundation with the following key features fully implemented:

-   🎙️ **Wake Word Detection**: Always listening for "Hey Loki" using the highly efficient Porcupine engine.

-   🔊 **Dynamic Command Recording**: The assistant doesn't record for a fixed duration. It uses Voice Activity Detection (VAD) to start recording when you speak and stop as soon as you finish, making interactions fast and natural.

-   🧠 **High-Accuracy Speech-to-Text**: Employs the `faster-whisper` library for transcription, with support for various model sizes and GPU acceleration to balance speed and accuracy.

-   ⚡ **Dual-Layer Intent Classification**:
    -   **Fast Path**: A high-speed, embedding-based classifier (`FastClassifier`) uses a powerful sentence-transformer model to instantly recognize and parse common commands with over 80% confidence.
    -   **LLM Fallback**: For any command that doesn't meet the fast path's confidence threshold, the query is passed to a local LLM (via Ollama) for more advanced, flexible intent recognition.

-   🤖 **Agent-Based Architecture**: LOKI's skills are modularized into "agents." The following agents are fully functional:
    -   `CalculationAgent`: Evaluates complex mathematical expressions (e.g., "what is the square root of 144 times 9?").
    -   `SystemControlAgent`: Performs basic OS tasks like launching applications (e.g., "open notepad").

-   🗣️ **Asynchronous Text-to-Speech (TTS)**: A non-blocking `TTSManager` synthesizes and speaks LOKI's responses in a background thread. This allows the assistant to start listening for the next command *while* it is still speaking, making it feel highly responsive.

-   ⚙️ **Fully Centralized Configuration**: All application settings—from model paths and AI model sizes to sensitivity thresholds—are managed in a single `.env` file for easy tuning and modification without changing code.

## Project Roadmap (What's Left to Port)

While the core AI pipeline is complete, this Python version is still a console application. The following features from the more mature C++ project are planned for future implementation:

-   🖥️ **Full GUI and System Tray Integration**:
    -   The C++ version is a complete desktop application that runs minimized in the system tray.
    -   It features a frameless, auto-hiding window that appears on wake-word detection to display real-time status and LOKI's response.

-   🔧 **Expanded System Control Agent**:
    -   **Volume Control**: The ability to increase, decrease, mute, unmute, and set system volume to a specific level.
    -   **Power Management**: Commands to shut down, restart, sleep, or log off the computer.

-   🌍 **New General Purpose Agent**:
    -   An agent to handle common queries like "what's the date?", "what's the weather like?", and perform web searches.

## Installation

Follow these steps to set up and run the LOKI voice assistant on your local machine.

### Prerequisites

-   **Python 3.11** or newer.
-   **Git** and **Git LFS** (Large File Storage).
-   **Ollama** for local LLM functionality.

### Step 1: Install Git LFS and Clone the Repository

This project uses Git LFS to manage the large AI model files. You must install it before cloning.

1.  **Install Git LFS**. If you don't have it, download it from the [official website](https://git-lfs.github.com/).

2.  **Initialize Git LFS** on your system. You only need to do this once per machine.
    ```bash
    git lfs install
    ```

3.  **Clone the Repository**. Git LFS will automatically download the large model files during this process.
    ```bash
    git clone https://github.com/Rudra-Garg/NLP-Project.git
    cd NLP-Project
    ```
    If the models did not download, you can pull them manually by running `git lfs pull` inside the repository.

### Step 2: Install and Set Up Ollama

Ollama serves the local LLM that LOKI uses for advanced understanding.

1.  **Download and Install Ollama** from the [official website](https://ollama.com/).

2.  **Pull the Default Model**. After installation, run the following command in your terminal to download the recommended model for LOKI.
    ```bash
    ollama pull dolphin-phi
    ```
    You can choose a different model, but be sure to update the `.env` file accordingly.

### Step 3: Set Up Python Environment

It is highly recommended to use a virtual environment.

1.  **Create the virtual environment**:
    ```bash
    python -m venv venv
    ```

2.  **Activate the environment**:
    -   **On Windows**:
        ```bash
        venv\Scripts\activate
        ```
    -   **On macOS and Linux**:
        ```bash
        source venv/bin/activate
        ```

### Step 4: Install Dependencies

With your virtual environment activated, install the required Python packages.
```bash
pip install -r requirements.txt
```

## Configuration

All application settings are controlled via a `.env` file for easy management.

1.  **Create the `.env` file**. In the project's root directory, make a copy of the example file and name it `.env`.

2.  **Add Your PicoVoice Access Key**. Open the new `.env` file and add your secret key. You can get one for free from the [Picovoice Console](https://console.picovoice.ai/).

    ```ini
    # .env
    
    # Get your free key from https://console.picovoice.ai/
    ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY_HERE"
    
    # ... (other settings are pre-configured)
    ```

3.  **(Optional) Tune LOKI's Behavior**. The `.env` file allows you to easily change the Whisper model size, switch to GPU processing, adjust VAD sensitivity, and more. Review the comments in the file to see what you can configure.

## Running LOKI

1.  **Start the Ollama Service**. Make sure the Ollama application is running in the background. It will automatically serve the LLM on your local machine.

2.  **Run the Main Application**. With your virtual environment activated, run the `main.py` script from your terminal:
    ```bash
    python main.py
    ```

LOKI will initialize all components. Once ready, you will see `Listening for 'Hey Loki'...` in the console. You can now start giving commands. To stop the application, press `Ctrl+C` in the terminal.

## How It Works: The Processing Pipeline

1.  **Wake Word**: The `pvporcupine` engine continuously listens for "Hey Loki" in the main audio stream.
2.  **Dynamic Recording**: Once triggered, LOKI uses Voice Activity Detection (VAD) to record your command, automatically stopping after it detects a pause.
3.  **Transcription**: The recorded audio is converted to text using `faster-whisper`.
4.  **Fast Path Classification**: The transcribed text is first sent to the `FastClassifier`. If it matches a known command template with high confidence, the intent is immediately dispatched.
5.  **LLM Fallback**: If the Fast Classifier is not confident, the text is sent to the local LLM via `Ollama` for a more nuanced classification.
6.  **Agent Execution**: The classified intent is dispatched to the appropriate agent (`CalculationAgent` or `SystemControlAgent`), which executes the required action.
7.  **Asynchronous Response**: The text response from the agent is sent to the `TTSManager`, which generates the audio and plays it in a background thread, allowing LOKI to immediately return to listening for the wake word.