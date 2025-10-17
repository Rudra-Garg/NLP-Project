# LOKI - Python Voice Assistant

## Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/loki-python.git
    cd loki-python
    ```

2.  **Set up Virtual Environment**
    ```bash
    python -m venv venv
    # Activate it
    # Windows: venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Decompress Assets**
    This project uses a script to manage large model and executable files. Run the following command to decompress the required assets:
    ```bash
    python manage_assets.py decompress
    ```
    This will create the `models/` and `piper/` directories needed by the application.

5.  **Configure Environment**
    Create a `.env` file in the root directory and add your Picovoice Access Key:
    ```
    ACCESS_KEY="YOUR_PICOVOICE_ACCESS_KEY_HERE"
    ```

6.  **Run LOKI**
    ```bash
    python main.py
    ```