# Edge AI–Powered AR Assistant

A real-time, **Edge AI–powered AR assistant** built during the **Qualcomm EdgeAI Hackathon**.  
The system combines **YOLOv8** (object detection) with **Llama 3.2B** running on **AnythingLLM (Snapdragon NPU)** for reasoning and step planning.  
A mobile frontend streams camera frames via **WebSockets**, receives instructions, and renders **AR overlays** (bounding boxes + text).

---

## Table of Contents

1. Purpose  
2. Implementation  
3. Setup  
4. Usage  
5. Troubleshooting  
6. Known Limitations & Fallback  
7. Contributing  
8. Code of Conduct  

---

## 1. Purpose

Industrial sectors like **manufacturing, aerospace, energy, and oil & gas** are losing tacit knowledge as experienced workers retire. Traditional training methods fail to support **field-based, dynamic workflows**.

This project demonstrates a **step-by-step AR task assistant** that runs **entirely on-device**:

- **Visual state detection** (YOLOv8)  
- **Reasoning & step generation** (Llama 3.2B on Snapdragon NPU via AnythingLLM)  
- **AR overlays** for real-time user guidance  

Our MVP task is guiding a user through an **Instant Pot workflow** — but the architecture is extensible to **assembly, inspection, and maintenance** in industrial environments.

---

## 2. Implementation

This system was built for the **Snapdragon X Elite Copilot+ PC** but designed to be platform agnostic.  

### Hardware

- **Machine**: Qualcomm Snapdragon X Elite PC (Dell Latitude 7455)  
- **OS**: Windows 11  
- **Memory**: 32 GB RAM  
- **AR Client**: Smartphone (camera + browser frontend)  

### Software Stack

- **Python 3.11 (64-bit)**  
- **FastAPI + Uvicorn** (backend server)  
- **WebSockets** (for streaming images + instructions)  
- **YOLOv8 (ONNX Runtime)** — object/button detection  
- **AnythingLLM (NPU runtime)** — runs Llama 3.2B reasoning model  
- **Frontend**: React (served from backend after `npm run build`)  
- **Certs**: mkcert for local HTTPS  
- **Messaging**: JSON step flows returned over WebSocket  

**Pipeline Overview**  
1. **Frontend (phone)** streams frames → **Backend** via WebSocket  
2. **Backend** runs YOLOv8 → gets bounding boxes  
3. Bounding boxes + user goal passed into **Llama 3.2B (AnythingLLM NPU)**  
4. LLM returns **next-step instructions**  
5. **Frontend** receives AR overlay data → draws boxes + guidance  

---

## 3. Setup

### Clone the repo
```powershell
git clone https://github.com/sankirthk/QEAI.git
cd QEAI
```

### Backend (Python environment)
```powershell
# 1. Create venv (Python 3.11, 64-bit)
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend (React build)
```powershell
cd frontend
npm install
npm run build
```
This generates a `build/` folder. The backend automatically serves this folder over HTTPS.

### Config
Create a `config.yaml` file in the backend root:
```yaml
api_key: "your-anythingllm-api-key"
model_server_base_url: "http://localhost:3001/api/v1"
workspace_slug: "your-workspace"
stream: true
stream_timeout: 60
```

### Certificates (HTTPS for phone browser)
```powershell
# Install mkcert
choco install mkcert

# Initialize
mkcert -install

# Create cert for loopback/local IP
mkcert 192.168.137.1
```
Copy the generated certs to your **phone** and install the profile so the browser trusts HTTPS.

### Hotspot (local Wi-Fi without internet)

1. **Add Loopback Adapter**  
   Device Manager → Add legacy hardware → Microsoft KM-TEST Loopback Adapter → Rename to `Loopback` → Restart  

2. **Run hotspot tether script**  
   Use the provided script to start the hotspot via the Loopback adapter:
   ```powershell
   .\scripts\start-hotspot.ps1
   ```

   > This powershell script uses the Loopback adapter to create a local-only hotspot, allowing your phone to connect even without internet.

3. **Disable Power Saving**  
   - Settings → Network & Internet → Mobile Hotspot → Power Saving **Off**  
   - Device Manager → Wireless Adapter → Properties → Power Management → uncheck "Allow computer to turn off device"  

---

## 4. Usage

Start the backend with HTTPS enabled:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 `
  --ssl-keyfile .\192.168.137.1-key.pem `
  --ssl-certfile .\192.168.137.1.pem
```

On your **phone** (connected to hotspot), open:  
👉 `https://192.168.137.1:8000/`

- Camera frames will stream to backend via WebSocket  
- YOLOv8 + Llama 3.2B pipeline will generate instructions  
- Bounding boxes + guidance text are rendered as AR overlays  

---

## 5. Troubleshooting

- **Browser blocks site** → Ensure you installed the mkcert cert on your phone.  
- **Hotspot doesn’t appear** → Run:
  ```powershell
  .\scripts\start-hotspot.ps1
  ```
  Ensure the Loopback adapter is renamed to `Loopback` and restart PC if needed.  
- **Inference not running on NPU** → Ensure you’re using **ARM64 ONNX Runtime** build + AnythingLLM NPU provider.  
- **Frontend not served** → Run `npm run build` inside `frontend/`.  

---

## 6. Known Limitations & Fallback

- Running **ML inference, backend server, frontend hosting, and hotspot creation simultaneously** on the Snapdragon PC can overload resources.  
- On phones, this sometimes causes **incomplete rendering or lag** in the browser.  
- **Fallback Mode:** You can instead run the frontend directly on the **laptop’s browser** and use the **laptop camera** as input.  
  - This bypasses hotspot networking overhead.  
  - Steps and overlays still function the same way, just without mobile AR.  

---

## 7. Contributing

Contributions welcome 🎉.  
Please open a PR to extend functionality (e.g., new workflows, better overlays, support for AR glasses).

---

## 8. Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).  
Be respectful, inclusive, and collaborative.

---

## 📜 License

MIT (or update with your license)

