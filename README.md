# QEAI
Got it ✅ — here’s a complete **`README.md`** you can drop directly into your repo. It merges the **hackathon execution plan + technical outline** from your uploaded docwith the **prereqs and run instructions** you listed.

````markdown
# Edge-AR-Assistant

An AR cooking/IoT assistant built for the **Qualcomm EdgeAI Hackathon**.  
The system uses **YOLOv8** for object detection, **ONNX Runtime** for inference on Snapdragon X PCs, and **MQTT** for real-time communication with a mobile frontend overlay.

---

## 📋 Prerequisites

- **Windows 10/11 (64-bit)**
- **Python 3.11 (64-bit)** installed and on PATH  
  Verify:
  ```powershell
  python --version
````

* **PowerShell** (Admin recommended for certificate setup)
* **mkcert** (for local HTTPS certs) → [Download](https://github.com/FiloSottile/mkcert/releases)
* **Mosquitto MQTT Broker**
* (Optional) OpenSSL for cert conversions

---

## 🚀 Quick Start

```powershell
# 1) Create & activate venv (Python 3.11, 64-bit)
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt    # or requirements.py if your repo uses that

# 3) Install num2word
pip install num2word

# 4) Run the setup script (attached in repo)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\setup.ps1

# 5) Create TLS cert for local IP (192.168.137.1)
mkcert -install
mkcert 192.168.137.1

# 6) Launch the app (replace with actual uvicorn entrypoint)
uvicorn main:app --host 0.0.0.0 --port 8000 `
  --ssl-keyfile .\192.168.137.1-key.pem `
  --ssl-certfile .\192.168.137.1.pem
```

Now open:
👉 `https://192.168.137.1:8000/`

---

## 🏗️ Architecture

**Device A (AR I/O):** Smartphone or a Camera I/O Device

* Streams camera frames
* Renders AR overlays (text + bounding boxes)

**Device B (Edge AI Brain):** Snapdragon X or X Elite PC

* Runs local ONNX inference
* Publishes instructions via WebSocket

---

## 🛠️ Tools & Stack

| Component        | Tool                                  |
| ---------------- | ------------------------------------- |
| Object detection | YOLOv8 (Ultralytics) / Grounding DINO |
| Inference        | ONNX Runtime on Snapdragon PC         |
| AR rendering     | Web frontend (HTML/JS + MQTT)         |
| Communication    | MQTT (Mosquitto) over Wi-Fi 6         |
| Device comm      | Flask API or WebRTC                   |
| Task logic       | JSON FSM (`task_flow.json`)           |

---

---

## 📜 License

Add your license info here (MIT, Apache-2.0, etc.)

```

---

Want me to also generate a **starter `task_flow.json`** and **`mqtt_client.py` template** so your repo has working scaffolds right away?
```
