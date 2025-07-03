# Project Repository

This is the initial README file for the project.

---

## ⚡️ Unified Backend/Frontend HTTPS/Port Alignment

- The frontend expects the backend to run at:  
  ```https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001```
- The frontend is served at HTTPS and port **3000**.  
- The backend **must be started with HTTPS, port 3001**, and a valid certificate.
- Ensure backend CORS is set to allow `https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3000`
  _No changes needed to backend env/.env configuration or to frontend .env, as long as you use the below command._

---

## 🚀 How To Start Backend (FastAPI/Uvicorn) for HTTPS on Port 3001

**Recommended (single command – dev and cloud-safe):**
```sh
cd royaltree_backend
bash start_https.sh
```

This script will:
- Ensure `ssl.crt` and `ssl.key` exist (run `generate_selfsigned_cert.sh` if missing)
- Start Uvicorn at `https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001` with HTTPS
- Enable auto-reload and debug logs

**Manual method (if needed):**
```sh
# Generate cert/key if missing
bash generate_selfsigned_cert.sh
# Or manually:
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl.key -out ssl.crt -subj "/CN=localhost"

# Start backend server:
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload \
  --ssl-keyfile ssl.key --ssl-certfile ssl.crt --log-level debug
```

---

## 🕵️ Verification (Backend/Frontend Cross-Service Requests)

- After backend is started (above), verify API root is live:
  ```sh
  curl -k https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/
  ```
  _(should return JSON: `{"platform": "Royaltree", ...}`)_

- Registration:
  ```sh
  curl -k -X POST https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"test1","email":"t1@example.com","role":"creator","password":"testing1"}'
  ```
- Login:
  ```sh
  curl -k -X POST https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test1&password=testing1"
  ```

- Test with browser:  
  - https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/docs

---

## 🧑‍💻 Restarting Both Services

Whenever you change code or configuration:

1. **Restart Backend (HTTPS):**
   ```sh
   cd royaltree_backend
   bash start_https.sh
   ```

2. **Restart Frontend**  
   - From frontend repo, e.g.:
    ```sh
    npm run start
    # Or (for Vite/Rapid toolchains):
    npm run dev
    ```

---

## ⚠️ Using a Non-Default Port/Protocol?

- If you ever must change backend port/protocol, update the frontend's `.env` variable to match:
    ```
    REACT_APP_API_BASE_URL=https://<your-backend-url>:<port>
    ```
  Then restart the frontend.

---

_For stepwise troubleshooting, request inspection, or live log watching, consult `SERVER_LOG_INSTRUCTIONS.md` for advanced diagnostics._