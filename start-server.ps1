# start-server.ps1
# 1. Start hotspot
& powershell -ExecutionPolicy Bypass -File ".\start-hotspot.ps1"

# 2. Activate venv
cd backend
.\.venv\Scripts\Activate.ps1

# 3. Run backend (example with uvicorn + TLS)
uv run uvicorn app.main:app `
  --host 0.0.0.0 --port 8443 `
  --ssl-certfile ./certs/dev-cert.pem `
  --ssl-keyfile ./certs/dev-key.pem
