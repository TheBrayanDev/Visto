# Visto

Desktop multilingual object detection & translation app. Detects objects from webcam, translates labels into a target language, speaks them aloud, and logs results to a database.

## Quick Start

### 1. Start the Database

```bash
docker compose up -d
```

### 2. Create & Activate a Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the App

```bash
python main.py
```

A window will open showing your webcam feed. Select a language, click **Translate**, and the top 5 detected objects will appear with their translations.

> **Note:** The first run downloads YOLOv8 and NLLB-200 models (~1.5 GB total). Subsequent runs work fully offline.

---

*Inspired by [Thing Translator](https://experiments.withgoogle.com/thing-translator) by Dan Motzenbecker & Google Creative Lab (2017). Visto is its local-first, fully offline counterpart — same concept, no cloud APIs.*
