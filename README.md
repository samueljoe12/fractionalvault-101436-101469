# Project Repository

This is the initial README file for the project.

## Backend HTTPS Run (FastAPI/Uvicorn)

To match the frontend expectation (`https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001`), **run the backend on port 3001 with HTTPS and a self-signed certificate**:

```sh
cd royaltree_backend
bash generate_selfsigned_cert.sh
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload \
  --ssl-keyfile ssl.key --ssl-certfile ssl.crt --log-level debug
```

This enables:
- API available at: https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/
- Matches frontend `.env` variable: `REACT_APP_API_BASE_URL=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001`

If you must use a different port or HTTP, also update the frontend `.env` accordingly.

For details, see `SERVER_LOG_INSTRUCTIONS.md`.