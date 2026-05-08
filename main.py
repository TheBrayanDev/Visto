import base64
import io
import subprocess
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select
from database import init_db, get_session
from models import ScanHistory
from ml_services import load_models, detect_objects, translate_text

yolo = None
tokenizer = None
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global yolo, tokenizer, model
    init_db()
    yolo, tokenizer, model = load_models()
    yield


app = FastAPI(title="Visto", lifespan=lifespan)


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")


class TranslateRequest(BaseModel):
    image: str
    target_lang: str


NLLB_LANG_TO_VOICE = {
    "spa_Latn": "es",
    "fra_Latn": "fr",
    "deu_Latn": "de",
    "jpn_Jpan": "ja",
}


def speak(text: str, target_lang: str = "eng_Latn"):
    lang_code = NLLB_LANG_TO_VOICE.get(target_lang)
    if not lang_code:
        return

    def _speak():
        try:
            subprocess.run(
                ["spd-say", "-l", lang_code, text],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            pass

    threading.Thread(target=_speak, daemon=True).start()


@app.post("/api/translate")
def translate(req: TranslateRequest, session: Session = Depends(get_session)):
    try:
        image_bytes = base64.b64decode(req.image)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image")

    detections = detect_objects(yolo, image_bytes)
    if not detections:
        return JSONResponse(content={"detections": [], "detection": None, "translation": None, "confidence": None})

    detections.sort(key=lambda d: d["confidence"], reverse=True)
    top5 = detections[:5]

    for d in top5:
        d["translation"] = translate_text(tokenizer, model, d["label"], req.target_lang)

    top = top5[0]

    record = ScanHistory(
        english_label=top["label"],
        translated_label=top["translation"],
        target_language=req.target_lang,
        confidence=top["confidence"],
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    speak(top["translation"], req.target_lang)

    return JSONResponse(content={
        "id": record.id,
        "detection": top["label"],
        "translation": top["translation"],
        "target_language": req.target_lang,
        "confidence": top["confidence"],
        "timestamp": record.timestamp.isoformat(),
        "detections": [
            {
                "label": d["label"],
                "translation": d["translation"],
                "confidence": d["confidence"],
            }
            for d in top5
        ],
    })
