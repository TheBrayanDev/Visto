# AI Agent Prompt: Project "Visto" (Full-Stack Multilingual)

**Role:** Act as a Senior Full-Stack Developer and Machine Learning Architect.

**Project Goal:** Build "Visto," an end-to-end local application that uses a webcam feed to detect objects and translate their names from English into a user-selected target language. The app must work entirely offline (after initial model download) and log results to a local database.

## Project Architecture

| Component        | Technology                          |
| ---------------- | ----------------------------------- |
| Project Name     | Visto                               |
| Database         | PostgreSQL 15-alpine (Docker)       |
| Backend          | FastAPI (Local venv)                |
| Frontend         | Vanilla HTML/JavaScript (Static via FastAPI) |
| ORM              | SQLModel (Strictly avoid standard SQLAlchemy) |
| Computer Vision  | YOLOv8 (ultralytics)                |
| Translation      | facebook/nllb-200-distilled-600M (Hugging Face) |
| Audio/TTS        | pyttsx3 (Local Text-to-Speech)      |

## Deliverables & File Structure

### 1. Infrastructure (docker-compose.yml & .env)

- Create a `docker-compose.yml` that initializes a PostgreSQL 15-alpine container and a pgAdmin4 container.
- Expose Postgres port 5432 to the host.
- Generate a `.env` template with:
  ```
  DATABASE_URL=postgresql://admin:password@localhost:5432/visto_db
  ```

### 2. Environment Setup (README.md & requirements.txt)

**requirements.txt:** Include `fastapi`, `uvicorn`, `sqlmodel`, `psycopg2-binary`, `ultralytics`, `transformers`, `torch`, `opencv-python`, `pyttsx3`, and `python-dotenv`.

**Documentation:** Provide a guide for:
- Starting Docker containers.
- Creating and activating the Python venv.
- Installing dependencies and launching the FastAPI server.

### 3. Backend Implementation (main.py, models.py, database.py, ml_services.py)

- **models.py:** Define a `ScanHistory` SQLModel including: `id`, `english_label`, `translated_label`, `target_language`, `confidence`, and `timestamp`.
- **database.py:** Setup the SQLModel engine and a `get_session` dependency. Include an `init_db()` function.
- **ml_services.py:** Use the FastAPI lifespan event to load YOLOv8 and the NLLB-200 model into memory once. Implement a translation function that accepts a `target_lang` code (e.g., `spa_Latn`, `fra_Latn`, `jpn_Jpan`).
- **main.py:**
  - Serve static files from a `/static` directory.
  - Endpoint: `POST /api/translate`
  - Logic: Detect object -> Translate label -> Trigger pyttsx3 for audio -> Save to Postgres -> Return JSON.

### 4. Frontend Implementation (static/index.html & static/app.js)

**index.html:** A modern UI branded as "Visto."
- `<video>` element for live webcam feed.
- `<select>` dropdown for target languages (Spanish, French, German, Japanese, and Chinese), mapping values to NLLB language codes.
- "Translate" button and a result display area.

**app.js:**
- Initialize webcam via `navigator.mediaDevices.getUserMedia`.
- On button click: Capture frame -> Convert to base64 -> Send to API with the selected `target_lang`.
- Dynamically update the UI with the translation and confidence score.

## Execution Instructions

- **Modularity:** Keep code clean and modular.
- **Resilience:** Implement "wait-for-db" logic or retries for the initial SQLModel connection to ensure the Docker container is ready.
- **Hardware:** Ensure pyttsx3 is initialized correctly to interface with local OS audio drivers.
- **Performance:** Move models to `cuda` if a GPU is available, otherwise default to `cpu`.
