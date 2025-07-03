# Backend Server Log Inspection, HTTPS Alignment, and Cross-Service Verification

To ensure the frontend and backend communicate reliably, the backend **must listen on HTTPS, port 3001** with a valid certificate. The frontend expects:
```
REACT_APP_API_BASE_URL=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001
```

## 1. Start/Relaunch the Backend on HTTPS Port 3001

### One-Step Recommended Launch:

```sh
# Start inside the backend directory
cd royaltree_backend
bash start_https.sh
```
This script:
- Checks for `ssl.key` and `ssl.crt` in the backend directory. If missing, runs `bash generate_selfsigned_cert.sh` to create a self-signed certificate for development.
- Launches Uvicorn:
  - Protocol: HTTPS
  - Host: 0.0.0.0
  - Port: 3001
  - Cert: `ssl.crt`
  - Key:  `ssl.key`
  - Auto-reload and debug logging enabled.

Access the backend at: **https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/**  
_(This matches the frontend .env variable; no backend or frontend code or env editing is necessary for port/protocol as long as this script is used.)_

### If Manual Launch is Needed:

```sh
# Generate certificate/key if missing
bash generate_selfsigned_cert.sh

# Or with pure OpenSSL:
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl.key -out ssl.crt -subj "/CN=localhost"

# Then launch Uvicorn manually
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload \
  --ssl-keyfile ssl.key --ssl-certfile ssl.crt --log-level debug
```

### To Restart the Backend

After making backend code or config changes, always re-run:
```sh
cd royaltree_backend
bash start_https.sh
```

---

## 2. Restart the Frontend

If you update `.env` (not usually required if backend is on :3001/https), restart the frontend service via:
```sh
# From frontend root directory
npm run start
# or for Vite/Parcel-based: npm run dev
```
_(Exact command may depend on frontend framework/tooling)_

---

## 3. Cross-Service Registration/Login - End-to-End Verification

### **a) Backend direct check with curl (bypass SSL warning with -k):**
```sh
curl -k https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/
```
Should respond with JSON including `"platform": "Royaltree"`.

### **b) Registration Example**
```sh
curl -k -X POST https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test1","email":"t1@example.com","role":"creator","password":"testing1"}'
```
Should return 201 Created and user info JSON, **and log a request** in the backend console.

### **c) Login Example**
```sh
curl -k -X POST https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test1&password=testing1"
```
Should return an access token JSON, **and log a request** in the backend logs.

---

## 4. Log Output Monitoring

- Make sure backend terminal output shows all incoming HTTP requests, CORS errors, and stack traces (DEBUG log level).
- If server logs are written to a file (e.g., if daemonized), use:
  ```sh
  tail -f /path/to/server.log
  ```
  Or view logs in the "Output" or "Terminal" window in VSCode or your IDE.

---

## 5. While Monitoring

1. Attempt registration and login from the **frontend web UI**.
2. Check: Does the backend log show `/auth/register` and `/auth/login` requests?
    - If **yes**, cross-service HTTPS is working.
    - If requests do **not appear**, check:
      - That both services are restarted
      - That ports/protocols/environment match
      - Network and CORS settings.

---

## 6. If You Must Use a Different Port or HTTP

- Update the frontend's `.env` variable:
  ```
  REACT_APP_API_BASE_URL=<actual-backend-url>
  ```
- Then restart the frontend service.

---

**Summary:**  
If you follow these steps, backend/HTTPS alignment and frontend/backend registration flow should work seamlessly. Use curl and browser at every step to confirm, and consult logs for issues.

