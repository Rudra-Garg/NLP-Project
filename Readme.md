# LOKI - A Modern Python Voice Assistant

LOKI is a private, responsive, and powerful voice assistant that runs entirely on your local machine. Built with a modern stack of local-first AI tools, it ensures your data remains yours.

The application operates from the system tray, activating a sleek, frameless GUI only when you say the wake word. Its core is a dual-layer intent classification system that handles common commands instantly and falls back to a local Large Language Model (LLM) for more complex queries.

[//]: # (![LOKI GUI Screenshot]&#40;placeholder.png&#41;  <!-- It's highly recommended to add a screenshot of your new GUI here! -->)

## Core Features

-   🎨 **Modern GUI & System Tray Integration**:
    -   LOKI runs quietly in your **system tray**, staying out of the way.
    -   On wake word detection, a beautiful, **frameless UI** fades into view to display the interaction.
    -   The UI provides real-time feedback, showing when LOKI is listening, processing, or responding, and then **automatically hides** itself.

-   🎙️ **Wake Word Detection**: Always listening for "Hey Loki" using the highly efficient Porcupine engine.

-   🔊 **Dynamic Command Recording**: LOKI doesn't record for a fixed duration. It uses Voice Activity Detection (VAD) to start recording when you speak and stop as soon as you finish, making interactions fast and natural.

-   🧠 **High-Accuracy Speech-to-Text**: Employs the `faster-whisper` library for transcription, with support for GPU acceleration.

-   ⚡ **Dual-Layer Intent Classification**:
    -   **Fast Path**: A high-speed, embedding-based classifier instantly recognizes common commands with high confidence.
    -   **LLM Fallback**: For any command that doesn't meet the fast path's confidence threshold, the query is passed to a local LLM (via Ollama) for more advanced, flexible intent recognition.

-   🤖 **Dynamic Agent Architecture**: LOKI's skills are modularized into "agents" that are **dynamically loaded** at startup. The following agents are fully functional:
    -   `CalculationAgent`: Evaluates complex mathematical expressions (e.g., "what is the square root of 144 times 9?").
    -   `SystemControlAgent`: Performs OS tasks like launching applications (e.g., "open notepad").
    -   `VolumeControlAgent`: Manages system volume with commands like "set volume to 75 percent."

-   🗣️ **Thread-Safe & Asynchronous**: The core assistant and TTS engine run in background threads, ensuring the GUI is always responsive. LOKI can start listening for the next command *while* it is still speaking.

-   ⚙️ **Clean & Structured Configuration**:
    -   All non-sensitive settings are managed in a clean, human-readable **`config.yaml`** file.
    -   Sensitive keys (like the PicoVoice Access Key) are kept separate and secure in a **`.env`** file.

## Project Roadmap

-   🔧 **Expanded System Control Agent**:
    -   **Power Management**: Commands to shut down, restart, sleep, or log off the computer.
-   🌍 **New General Purpose Agent**:
    -   An agent to handle common queries like "what's the date?", "what's the weather like?", and perform web searches.

## Installation

### Prerequisites

-   **Python 3.11** or newer.
-   **Git** and **Git LFS** (Large File Storage).
-   **Ollama** for local LLM functionality.

### Step 1: Install Git LFS and Clone the Repository

This project uses Git LFS to manage the large AI model files. You must install it before cloning.

1.  **Install Git LFS** from the [official website](https://git-lfs.github.com/).
2.  **Initialize Git LFS** (only needs to be done once per machine):
    ```bash
    git lfs install
    ```
3.  **Clone the Repository**. Git LFS will automatically download the models.
    ```bash
    git clone https://github.com/Rudra-Garg/NLP-Project.git
    cd NLP-Project
    ```
    If models did not download, run `git lfs pull` inside the repository.

### Step 2: Install and Set Up Ollama

1.  **Download and Install Ollama** from the [official website](https://ollama.com/).
2.  **Pull the Default Model** recommended for LOKI:
    ```bash
    ollama pull dolphin-phi
    ```

### Step 3: Set Up Python Environment

It is highly recommended to use a virtual environment.

1.  **Create and activate the environment**:
    ```bash
    # Create
    python -m venv venv
    
    # Activate (Windows)
    venv\Scripts\activate
    
    # Activate (macOS/Linux)
    source venv/bin/activate
    ```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

LOKI uses a clean, two-file configuration system.

1.  **Create the `config.yaml` file**: In the project's root directory, make a copy of `config.yaml.example` and name it `config.yaml`. (If no example file exists, just create an empty one and copy the structure from the project page).
2.  **Create the `.env` file**: Create a file named `.env` in the root directory.
3.  **Add Your PicoVoice Access Key**: Open the `.env` file and add your secret key. You can get one for free from the [Picovoice Console](https://console.picovoice.ai/).

    ```ini
    # .env
    ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY_HERE"
    ```

4.  **(Optional) Tune LOKI's Behavior**: Open `config.yaml` to change the Whisper model size, adjust VAD sensitivity, select a different LLM model, and more. The comments in the file explain what each setting does.

## Running LOKI

1.  **Start the Ollama Service**: Make sure the Ollama application is running in the background.
2.  **Run the GUI Application**: With your virtual environment activated, run the `gui.py` script:
    ```bash
    python gui.py
    ```
LOKI will start in the background and an icon will appear in your system tray. The application is now ready. Say "Hey Loki" to begin an interaction.

-   **To close LOKI**: Right-click the system tray icon and select "Quit".

-   **For a console-only experience**: You can run `python main.py`. Press `Ctrl+C` to stop.

## How It Works: The Processing Pipeline

1.  **System Tray**: The application starts minimized in the system tray, managed by the main GUI thread.
2.  **Background Worker**: The core logic (`LokiWorker`) runs in a separate, non-blocking thread.
3.  **Wake Word**: The worker continuously listens for "Hey Loki".
4.  **GUI Activation**: Upon wake word detection, the worker sends a signal to the main thread to fade in the GUI window.
5.  **Dynamic Recording & Transcription**: LOKI uses VAD to record the command and `faster-whisper` to transcribe it to text.
6.  **Intent Pipeline**:
    *   The transcript is first sent to the **`FastClassifier`** for instant recognition.
    *   If confidence is low, it falls back to the local **`LLMClassifier`** for more nuanced understanding.
    *   A **NER model** then extracts parameters (like application names or math expressions) from the text.
7.  **Agent Execution**: The final intent is dispatched to the appropriate agent (`Calculation`, `SystemControl`, etc.) which executes the action.
8.  **Asynchronous Response**: The text response is sent to the `TTSManager`, which generates and plays the audio in another background thread. The response is also displayed in the GUI.
9.  **GUI Deactivation**: After the interaction, the GUI automatically fades out and the assistant returns to listening for the wake word.