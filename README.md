# Project Repository

This is the initial README file for the project.

## Backend HTTPS Run (FastAPI/Uvicorn)

To match the frontend expectation (`https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001`), **run the backend on port 3001 with HTTPS and a self-signed certificate**:

**Recommended (one-step):**
```sh
cd royaltree_backend
bash start_https.sh
```

The script ensures the necessary SSL certificate and key are present, then launches FastAPI/Uvicorn:
- Runs at: https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/
- Matches frontend `.env` variable: `REACT_APP_API_BASE_URL=https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001`

**Manual method:**  
If needed, generate cert/key then launch manually:
```sh
bash generate_selfsigned_cert.sh
uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload \
  --ssl-keyfile ssl.key --ssl-certfile ssl.crt --log-level debug
```

### Verification

After starting the backend, check API availability with:
```sh
# Should succeed (bypassing cert validation in dev)
curl -k https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/
```
You should see JSON with `"platform": "Royaltree"` if all is configured correctly.

You can also open the API docs in your browser:
- [https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/docs](https://vscode-internal-8323-beta.beta01.cloud.kavia.ai:3001/docs)

If you must use a different port or HTTP, **update the frontend `.env` accordingly** to match.

For details, see `SERVER_LOG_INSTRUCTIONS.md`.