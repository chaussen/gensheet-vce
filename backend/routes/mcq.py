import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.mcq_engine import generate_mcq, submit_mcq
from backend.services.session_limiter import SessionLimitExceeded

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/mcq")


class GenerateRequest(BaseModel):
    topic_code: str


class SubmitRequest(BaseModel):
    session_id: str
    answers: list[str]


@router.post("/generate")
async def generate(req: GenerateRequest):
    try:
        result = await generate_mcq(req.topic_code)
        if "error" in result:
            raise HTTPException(status_code=500, detail="generation_failed")
        return result
    except SessionLimitExceeded:
        raise HTTPException(status_code=429, detail="session_limit_reached")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unhandled error in /api/mcq/generate: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="generation_failed")


@router.post("/submit")
async def submit(req: SubmitRequest):
    try:
        result = submit_mcq(req.session_id, req.answers)
        return result
    except KeyError as e:
        if "session_not_found" in str(e):
            raise HTTPException(status_code=404, detail="Session expired. Please start a new session.")
        raise HTTPException(status_code=404, detail="Not found.")
