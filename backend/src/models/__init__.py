from typing import *

from .contest import ContestRegistrationPublic, ContestRegistrationOut, ContestRegistration, ContestPublic, ContestView, Contest
from .user import UserPublic, UserView, User
from .problem import ProblemPublic, ProblemView, Problem
from .submission import SubmissionPublic, SubmissionView, Submission, SUBMISSION_STATUS, SUBMISSION_VERDICT
from .hack import HackPublic, Hack


class SubmissionListOut(SubmissionPublic):
    user: UserPublic
    problem: ProblemPublic
    contest_registration: Optional[ContestRegistrationOut] = None


class SubmissionDetailOut(SubmissionView):
    user: UserPublic
    problem: ProblemPublic
    contest_registration: Optional[ContestRegistrationOut] = None


__all__ = [
    "ContestRegistrationPublic", "ContestRegistrationOut", "ContestRegistration", "ContestPublic", "ContestView", "Contest",
    "UserPublic", "UserView", "User",
    "ProblemPublic", "ProblemView", "Problem",
    "SubmissionPublic", "SubmissionView", "SubmissionListOut", "SubmissionDetailOut", "Submission", "SUBMISSION_STATUS", "SUBMISSION_VERDICT",
    "HackPublic", "Hack",
]
