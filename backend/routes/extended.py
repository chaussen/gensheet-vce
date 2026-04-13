import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.extended_engine import generate_extended, get_solution
from backend.services.session_limiter import SessionLimitExceeded

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/extended")


class GenerateRequest(BaseModel):
    topic_code: str
    difficulty: str = "standard"


class SolutionRequest(BaseModel):
    session_id: str
    question_index: int
    part_label: str


@router.post("/generate")
async def generate(req: GenerateRequest):
    try:
        result = await generate_extended(req.topic_code, req.difficulty)
        return result
    except SessionLimitExceeded:
        raise HTTPException(status_code=429, detail="session_limit_reached")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unhandled error in /api/extended/generate: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="generation_failed")


@router.post("/solution")
async def solution(req: SolutionRequest):
    try:
        sol = get_solution(req.session_id, req.question_index, req.part_label)
        return {"worked_solution_latex": sol}
    except KeyError as e:
        if "session_not_found" in str(e):
            raise HTTPException(status_code=404, detail="Session expired. Please start a new session.")
        raise HTTPException(status_code=404, detail="Part not found.")
