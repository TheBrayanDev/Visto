# Visto

Full-stack multilingual object detection & translation app. Detects objects from webcam, translates labels into a target language, speaks them aloud, and logs results to a database.

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

### 4. Launch the Server

```bash
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser, grant webcam access, and start translating.

> **Note:** The first run downloads YOLOv8 and NLLB-200 models (~1.5 GB total). Subsequent runs work fully offline.
