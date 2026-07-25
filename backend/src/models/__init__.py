from typing import *

from .links import ContestTask, ContestRegistration
from .user import UserPublic, UserView, User
from .problem import ProblemPublic, ProblemView, Problem
from .submission import SubmissionPublic, SubmissionView, Submission, SUBMISSION_STATUS, SUBMISSION_VERDICT
from .contest import ContestPublic, ContestView, Contest

class ContestView(ContestView):
    problems: list["ProblemPublic"] | None


class SubmissionPublic(SubmissionPublic):
    user: "UserPublic"
    contest: Optional["ContestPublic"]
    problem: "ProblemPublic"


class SubmissionView(SubmissionView):
    user: "UserPublic"
    contest: Optional["ContestPublic"]
    problem: "ProblemPublic"


__all__ = [
    "ContestTask", "ContestRegistration",
    "UserPublic", "UserView", "User",
    "ProblemPublic", "ProblemView", "Problem",
    "ContestPublic", "ContestView", "Contest",
    "SubmissionPublic", "SubmissionView", "Submission", "SUBMISSION_STATUS", "SUBMISSION_VERDICT",

    "ContestView"
]

