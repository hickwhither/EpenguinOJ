from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from src.database import SessionDep
from src.models import Problem
from pathlib import Path

# CONFIGURATIONS
router = APIRouter(prefix="/judger", tags=["webhook.judger"])

BASE_PROBLEMS_DIR = Path("tmp/problems").resolve()

@router.get('/{id}')
@router.get('/{id}/{path:path}')
async def serve_file(session: SessionDep, id: int, path: str | None = None):
    if not path:
        problem = await session.get(Problem, id)
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")
        return problem.batches

    problem_dir = (BASE_PROBLEMS_DIR / str(id)).resolve()
    file_path = (problem_dir / path).resolve()
    if not str(file_path).startswith(str(problem_dir)) or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found or access denied")
    return FileResponse(path=file_path)