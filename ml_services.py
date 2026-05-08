import io
import numpy as np
import cv2
from PIL import Image

device = "cpu"


def load_models():
    global device
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"

    from ultralytics import YOLO
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    yolo = YOLO("yolov8n.pt")

    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)

    return yolo, tokenizer, model


def detect_objects(yolo, image_bytes: bytes) -> list[dict]:
    img = Image.open(io.BytesIO(image_bytes))
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    results = yolo(img)[0]

    detections = []
    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = results.names[cls_id]
        conf = float(box.conf[0])
        detections.append({"label": label, "confidence": conf})

    return detections


def translate_text(tokenizer, model, text: str, target_lang: str) -> str:
    inputs = tokenizer(text, return_tensors="pt").to(device)
    forced_bos_token_id = tokenizer.convert_tokens_to_ids(target_lang)
    outputs = model.generate(**inputs, forced_bos_token_id=forced_bos_token_id, max_length=128)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)
