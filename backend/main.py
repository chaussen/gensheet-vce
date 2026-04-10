import logging
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from datetime import datetime, timezone
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routes.extended import router as extended_router
from backend.routes.mcq import router as mcq_router

app = FastAPI(title="GenSheet VCE")

@app.head("/api/health", include_in_schema=False)
async def health_head():
    """Explicit HEAD handler for UptimeRobot (free tier only supports HEAD)."""
    return Response(status_code=200)


@app.get("/api/health")
async def health():
    """Keep-alive endpoint — pinged by UptimeRobot every 14 min in production."""
    return {
        "status": "ok",
        "ts": datetime.now(timezone.utc).isoformat(),
    }

app.include_router(extended_router)
app.include_router(mcq_router)

# Serve frontend static files (built by Vite)
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)
