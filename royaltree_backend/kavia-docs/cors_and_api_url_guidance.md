# Royaltree: Frontend/Backend Port and CORS/URL Alignment Guide

For correct operation, the frontend and backend must agree on the **protocol (HTTP/HTTPS)**, **host**, and **port**.

---

## 1. Backend: Allowing Frontend Origin (CORS)

Backend CORS is controlled by the `FRONTEND_ORIGINS` environment variable.

- **Default:** `https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3000`
- **If you start the frontend on a different port or hostname:**  
  Set `FRONTEND_ORIGINS` to match your frontend’s full URL.

**How to override (Unix/bash example):**
```sh
export FRONTEND_ORIGINS=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:4000
# Then (from backend folder):
bash start_https.sh
```

You may also set this in your `.env` file in the backend root, e.g.:
```
FRONTEND_ORIGINS=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:4000
```

**Multiple origins:** Separate with commas (no spaces).

---

## 2. Frontend: Setting the Backend API Base URL

Your React frontend needs to know the backend API base URL.  
This is defined in `.env` in the frontend codebase as:

```
REACT_APP_API_BASE_URL=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001
```

- If you **change the backend port** (e.g., run backend on 4001 instead of 3001), update this variable and restart the frontend.
- Ensure both backend and frontend use **HTTPS** for secure, error-free communication.

_Whenever you change the backend port/protocol or the frontend host/port, check:_
- `FRONTEND_ORIGINS` in backend matches the frontend URL exactly (including port, protocol).
- `REACT_APP_API_BASE_URL` in frontend matches backend's reachable base URL.

---

**If you see CORS errors or failed API calls in the browser console, double-check these variables!**

---
