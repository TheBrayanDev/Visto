const video = document.getElementById("webcam");
const translateBtn = document.getElementById("translateBtn");
const langSelect = document.getElementById("langSelect");
const resultDiv = document.getElementById("result");
const resultValue = document.getElementById("resultValue");
const resultMeta = document.getElementById("resultMeta");
const errorDiv = document.getElementById("error");

let stream = null;

async function initWebcam() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
  } catch {
    showError("Webcam access denied. Please grant camera permissions.");
  }
}

function showError(msg) {
  errorDiv.textContent = msg;
}

function clearError() {
  errorDiv.textContent = "";
}

function captureFrame() {
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0);
  return canvas.toDataURL("image/jpeg", 0.8).split(",")[1];
}

translateBtn.addEventListener("click", async () => {
  clearError();
  translateBtn.disabled = true;
  translateBtn.innerHTML = '<span class="spinner"></span>Translating...';

  try {
    const image = captureFrame();
    const targetLang = langSelect.value;

    const res = await fetch("/api/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image, target_lang: targetLang }),
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || "Translation failed");
      return;
    }

    if (data.detection) {
      const list = data.detections.map((d, i) =>
        `<div class="detection-item">
          <span class="rank">${i + 1}</span>
          <span class="detect-label">${d.label}</span>
          <span class="arrow">→</span>
          <span class="detect-translation">${d.translation}</span>
          <span class="detect-conf">${(d.confidence * 100).toFixed(1)}%</span>
        </div>`
      ).join("");
      resultValue.innerHTML = list;
      resultMeta.textContent = `Language: ${langSelect.options[langSelect.selectedIndex].text}`;
      resultDiv.classList.add("visible");
    } else {
      showError("No objects detected. Try a different angle or lighting.");
    }
  } catch {
    showError("Network error. Is the server running?");
  } finally {
    translateBtn.disabled = false;
    translateBtn.textContent = "Translate";
  }
});

initWebcam();
