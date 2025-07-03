# Backend Server Log Inspection (FastAPI/Uvicorn)

To troubleshoot frontend/backend integration and determine if HTTP requests (especially `/auth/register` and `/auth/login`) reach the backend:

## 1. Start the FastAPI (Uvicorn) Server with Verbose Logging

If not already running, launch the backend with:
```sh
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
# or, e.g.:
# uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload --log-level debug
```

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
