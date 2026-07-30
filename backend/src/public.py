from pydantic import BaseModel
from typing import Any


#Submission
class SubmissionPublic(BaseModel):
    id: int

    # Cell 1
    percentage: float | None
    max_score: float | None
    status: str
    language: str

    # Cell 2
    problem: "ProblemPublic"
    user: "UserPublic"
    date_created: int
    # + Admin buttons

    # Cell 3
    time_used: float | None
    memory_used: float | None
    test_cases: list[dict[str, Any]] | None


class SubmissionView(SubmissionPublic):
    source: str
