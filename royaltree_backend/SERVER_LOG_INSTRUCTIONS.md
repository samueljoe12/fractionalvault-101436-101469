# Backend Server Log Inspection (FastAPI/Uvicorn)

To troubleshoot frontend/backend integration and determine if HTTP requests (especially `/auth/register` and `/auth/login`) reach the backend:

## 1. Start the FastAPI (Uvicorn) Server with Verbose Logging

If not already running, launch the backend on HTTPS, port 3001 (to match the frontend expectation) with a self-signed certificate:
```sh
# Generate self-signed cert (if not yet present)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ssl.key -out ssl.crt -subj "/CN=localhost"

# Recommended RUN command (for cloud/dev or local)
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload --ssl-keyfile ssl.key --ssl-certfile ssl.crt --log-level debug
```
- The API is then accessible at: **https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/**
- This configuration matches the frontend `.env` variable: `REACT_APP_API_BASE_URL=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001`
- If you want to use a different port or HTTP only, make sure the frontend `.env` is also updated to match.

# CORS: Check main.py for allowed origins! Make sure the backend allows the actual deployed frontend origin and protocol.

This enables stdout log output for all incoming requests, CORS issues, errors, and stack traces.

## 2. Log File Monitoring (if server runs as daemonized process)

If logs are piped to a file, view them with:
```sh
tail -f /path/to/server.log
```
or inside VSCode, use the "Output" or "Terminal" window associated with the backend.

## 3. While Watching Logs

- Attempt registration/login from the frontend UI (`/register`, `/login`).
- Observe:
  - Does a request appear for `/auth/register` or `/auth/login`?
  - If so, is there an error/stacktrace or a normal 2xx/4xx response line?
  - If nothing appears, this points to proxy/network/firewall or CORS preflight failure.

## 4. Note

- If running in cloud/dev container, ensure you have access to the backend's live log output.
- After debugging, stop the log (Ctrl+C or kill the tail process if backgrounded).
