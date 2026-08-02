import random
import time
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query
import httpx
from pydantic import BaseModel

router = APIRouter(prefix="/solo", tags=["user.codeforces_solo"])

# InMemory Storage lưu trạng thái các phiên luyện tập
# Trong thực tế sản phẩm lớn, bạn có thể thay thế bằng Redis hoặc DB (PostgreSQL, MongoDB)
sessions_db: Dict[str, dict] = {}


# --- Models ---
class CreateSessionRequest(BaseModel):
    handle: str
    min_rating: int = 800
    max_rating: int = 1400
    tag: Optional[str] = None  # Ví dụ: "dp", "math", "greedy"


class SoloSessionResponse(BaseModel):
    session_id: str
    handle: str
    problem_name: str
    problem_url: str
    rating: Optional[int]
    start_time: float
    status: str  # "IN_PROGRESS", "PASSED"


# --- Helper Functions ---
async def fetch_random_problem(min_rating: int, max_rating: int, tag: Optional[str] = None) -> dict:
    url = "https://codeforces.com/api/problemset.problems"
    params = {}
    if tag:
        params["tags"] = tag

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Không thể kết nối đến Codeforces API")

        data = response.json()
        if data.get("status") != "OK":
            raise HTTPException(status_code=400, detail="Codeforces API trả về lỗi")

        problems = data["result"]["problems"]

        # Lọc bài tập theo mức Rating phù hợp
        eligible_problems = [
            p for p in problems
            if "rating" in p and min_rating <= p["rating"] <= max_rating
        ]

        if not eligible_problems:
            raise HTTPException(
                status_code=404, 
                detail=f"Không tìm thấy bài tập phù hợp trong tầm rating {min_rating}-{max_rating}"
            )

        return random.choice(eligible_problems)


async def check_user_submission(handle: str, contest_id: int, index: str, start_time: float) -> bool:
    """Kiểm tra xem handle đã nộp bài AC sau mốc start_time hay chưa."""
    url = f"https://codeforces.com/api/user.status?handle={handle}&from=1&count=10"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        if response.status_code != 200:
            return False

        data = response.json()
        if data.get("status") != "OK":
            return False

        submissions = data["result"]
        for sub in submissions:
            # Kiểm tra xem submission có thuộc bài tập này và nộp sau thời gian bắt đầu solo không
            problem = sub.get("problem", {})
            if (
                problem.get("contestId") == contest_id
                and problem.get("index") == index
                and sub.get("verdict") == "OK"
                and sub.get("creationTimeSeconds", 0) >= start_time
            ):
                return True

    return False


# --- Endpoints ---

@router.post("/start", response_model=SoloSessionResponse)
async def start_solo_session(payload: CreateSessionRequest):
    """
    Tạo mới một phiên solo: Chọn ngẫu nhiên 1 bài tập theo yêu cầu.
    """
    problem = await fetch_random_problem(
        min_rating=payload.min_rating,
        max_rating=payload.max_rating,
        tag=payload.tag
    )

    contest_id = problem["contestId"]
    index = problem["index"]
    problem_url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"

    session_id = f"{payload.handle}_{int(time.time())}"
    start_time = time.time()

    session_data = {
        "session_id": session_id,
        "handle": payload.handle,
        "contest_id": contest_id,
        "index": index,
        "problem_name": f"{contest_id}{index} - {problem.get('name')}",
        "problem_url": problem_url,
        "rating": problem.get("rating"),
        "start_time": start_time,
        "status": "IN_PROGRESS"
    }

    sessions_db[session_id] = session_data

    return SoloSessionResponse(
        session_id=session_id,
        handle=payload.handle,
        problem_name=session_data["problem_name"],
        problem_url=problem_url,
        rating=session_data["rating"],
        start_time=start_time,
        status="IN_PROGRESS"
    )


@router.get("/session/{session_id}", response_model=SoloSessionResponse)
async def get_session_info(session_id: str):
    """
    Lấy thông tin của phiên solo hiện tại.
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên làm bài")
    
    sess = sessions_db[session_id]
    return SoloSessionResponse(
        session_id=sess["session_id"],
        handle=sess["handle"],
        problem_name=sess["problem_name"],
        problem_url=sess["problem_url"],
        rating=sess["rating"],
        start_time=sess["start_time"],
        status=sess["status"]
    )


@router.post("/verify/{session_id}")
async def verify_solo_solution(session_id: str):
    """
    Gọi endpoint này để check xem bạn đã làm xong (Accepted) bài tập trên Codeforces chưa.
    """
    if session_id not in sessions_db:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên làm bài")

    sess = sessions_db[session_id]

    if sess["status"] == "PASSED":
        return {"status": "PASSED", "message": "Bạn đã hoàn thành bài tập này trước đó rồi!"}

    # Verify với Codeforces API
    is_ac = await check_user_submission(
        handle=sess["handle"],
        contest_id=sess["contest_id"],
        index=sess["index"],
        start_time=sess["start_time"]
    )

    if is_ac:
        sess["status"] = "PASSED"
        elapsed_time = round(time.time() - sess["start_time"])
        return {
            "status": "PASSED",
            "message": f"Chúc mừng! Bạn đã giải thành công bài tập sau {elapsed_time} giây.",
            "elapsed_seconds": elapsed_time
        }

    return {
        "status": "IN_PROGRESS",
        "message": "Chưa ghi nhận kết quả Accepted mới. Hãy nộp bài trên Codeforces rồi thử lại!"
    }