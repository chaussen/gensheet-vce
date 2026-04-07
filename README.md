# GenSheet VCE

VCE Specialist Mathematics exam practice — Year 12.

## Prerequisites

- Python 3.11+ with venv at `venv/`
- Node.js 18+

## Setup

Copy `.env` and fill in your key:
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...
```

## Development

**Backend** (from project root):
```bash
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Frontend** (in a second terminal):
```bash
cd frontend
npm run dev
```

Frontend dev server proxies `/api` to `localhost:8000`.
Open http://localhost:5173.

## Production build

```bash
cd frontend && npm run build
# Then start the backend — it serves the built frontend as static files
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Deploy (Render)

Push to GitHub. Create a new Web Service pointing to the repo.
Set `ANTHROPIC_API_KEY` in the Render environment variables.
`render.yaml` handles the rest.
