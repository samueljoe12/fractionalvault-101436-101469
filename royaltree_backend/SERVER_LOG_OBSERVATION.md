# Royaltree Backend (FastAPI/Uvicorn)
## Log Monitoring During Frontend Registration/Login Attempts

### Log Monitoring Setup

Launched the backend server in verbose (debug) mode with:

```sh
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### Observational Protocol

- Attempt registration and login via the frontend web UI (`/register`, `/login`).
- Monitor the server logs in the running process terminal for:
  - Arrival of HTTP requests (`/auth/register`, `/auth/login`).
  - Any FastAPI/Starlette log lines about requests, CORS, or responses.
  - Error reports, stack traces, or warnings.

---

### LOG OBSERVATIONS

- [ ] **1. Incoming Request Status**
  - [ ] No HTTP request from frontend appears in the logs (possible network/proxy/CORS/preflight block).
  - [ ] HTTP requests are received and visible as expected.

- [ ] **2. Error/Stack Trace**
  - [ ] No error/stack trace is generated.
  - [ ] Error/exception lines (with stack traces) appear (paste below if observed):

```text
# Paste error log lines or stack traces here if any observed.
```

- [ ] **3. CORS/Ignored or Blocked Request Evidence**
  - [ ] CORS or preflight failure observed (describe details below, e.g., 403/404/blocked origins).

---

### SUMMARY

- Observation notes:
  - If HTTP requests do not appear, this strongly suggests a frontend-to-backend network path, proxy, or CORS issue (no authentication/validation code is executed).
  - If requests appear but trigger errors, further debug per stack trace.
  - If everything functions, normal 2xx or 4xx response log lines should be visible.
- Please update the status checkboxes above with actual results after verifying with live frontend attempts.

---

_Task performed: Real-time backend log monitoring for frontend registration/login issues._
