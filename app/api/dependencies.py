from typing import Annotated

from fastapi import Depends, Request

from app.infrastructure.repositories import (
    SqlCourseRepository, SqlEnrollmentRepository, SqlUserRepository,
)
from app.services.study_manager import StudyManager


def get_service(request: Request):
    with request.app.state.session_factory() as session:
        yield StudyManager(SqlUserRepository(session), SqlCourseRepository(session),
                           SqlEnrollmentRepository(session))


Service = Annotated[StudyManager, Depends(get_service)]
