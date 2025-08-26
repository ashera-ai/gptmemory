# FastAPI on Render — Minimal Data Store

A tiny FastAPI service with:
- `POST /data` — stores whatever JSON you send
- `GET /data` — returns everything ever posted

## Quickstart (local)

```bash
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
