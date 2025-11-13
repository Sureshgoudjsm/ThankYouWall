# ThankYouWall 🎂

A Streamlit prototype app to convert birthday/DM screenshots into a single, shareable "thank you" image.

## Features

* **Multi-Image Upload:** Upload multiple screenshots at once.
* **Local OCR:** Uses Tesseract (via `pytesseract`) to extract text locally. No cloud upload by default.
* **Wish Editor:** Edit extracted names, messages, and timestamps in a clean UI.
* **Photo Upload:** Attach a profile photo for each wisher.
* **Privacy Controls:** Automatically blurs phone numbers and provides toggles to anonymize entries.
* **PNG Export:** Generates a single 1080x1350 PNG, perfect for Instagram Stories or posts.
* **Metadata Export:** Download all your data as a JSON or CSV file.

## ⚠️ Important Prerequisites: Install Tesseract

`pytesseract` is a Python *wrapper* for Google's Tesseract-OCR Engine. You **must** install Tesseract on your system *before* running the Python app.

### On macOS
```bash
brew install tesseract
```

### On Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### On Windows
1.  Download the official installer from the [Tesseract GitHub Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
2.  Run the installer. **Important:** Make note of the installation path (e.g., `C:\Program Files\Tesseract-OCR`).
3.  Add this Tesseract directory to your system's `PATH` environment variable.

## How to Run

1.  **Clone this repository or save the files**
    Save `app.py`, `requirements.txt`, and this `README.md` to a new folder.

2.  **Create a virtual environment (Recommended)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On macOS/Linux
    .\venv\Scripts\activate   # On Windows
    ```

3.  **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```
    
4.  **(Optional) Install Fonts**
    The PNG export script tries to find `Arial.ttf`. If you don't have it, the image may look bad. You can:
    * Install the `msttcorefonts` package (Linux).
    * Download a free font like [DejaVu Sans](https://www.fontsquirrel.com/fonts/dejavu-sans) (DejaVuSans.ttf) and place it in the same directory.
    * Edit `app.py` to point to a font file you know is on your system.

5.  **Run the Streamlit app**
    ```bash
    streamlit run app.py
    ```

A browser window will open automatically, pointing to your local app.

## Privacy Notice

This application is designed to be **privacy-first**.
* All OCR processing happens **locally on your computer**.
* Your screenshots are **never uploaded** to any server.
* The (optional) Google Vision API feature is disabled by default and not implemented in this prototype.
* All data is stored in your browser's session and is **cleared** when you close the tab (unless you export it).
