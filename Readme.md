# LOKI - Python Voice Assistant

## Installation

Follow these steps to set up and run the LOKI voice assistant on your local machine. This project uses Git LFS (Large File Storage) to manage the large model files required for operation.

### Prerequisites

Before you begin, ensure you have the following installed:
*   **Python 3.11** or newer.
*   **Git**.
*   **Git LFS** (Large File Storage).

### Step 1: Install Git LFS

If you do not have Git LFS installed, you need to install it first. You can download it from the [official website](https://git-lfs.github.com/).

After installing, run the following command in your terminal to initialize Git LFS on your system. You only need to do this once per machine.
```bash
git lfs install
```

### Step 2: Clone the Repository

Clone the repository using Git. During the clone process, Git LFS will automatically detect the `.gitattributes` file and download the large model files stored in the `models/` and `piper/` directories.

```bash
git clone https://github.com/Rudra-Garg/NLP-Project.git
cd NLP-Project
```

If the large files did not download automatically during the clone, you can pull them manually by running the following command inside the repository directory:
```bash
git lfs pull
```

### Step 3: Set up a Virtual Environment

It is highly recommended to use a virtual environment to manage the project's dependencies and avoid conflicts with other Python projects.

```bash
# Create the virtual environment
python -m venv venv
```

Activate the environment:
*   **On Windows**:
    ```bash
    venv\Scripts\activate
    ```
*   **On macOS and Linux**:
    ```bash
    source venv/bin/activate
    ```

### Step 4: Install Dependencies

With your virtual environment activated, install the required Python packages using pip.
```bash
pip install -r requirements.txt
```

### Step 5: Configure Your Environment

The application requires an Access Key from Picovoice for wake word detection.

1.  Create a file named `.env` in the root directory of the project.
2.  Add your Picovoice Access Key to this file. You can get a key for free from the [Picovoice Console](https://console.picovoice.ai/).

```
ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY_HERE"
```

### Step 6: Run LOKI

You are now ready to run the application.
```bash
python main.py
```

LOKI will initialize all components and, once ready, will print `Listening for 'Hey Loki'...` in the console.