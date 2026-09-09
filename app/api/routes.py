from typing import Annotated

from fastapi import APIRouter, Path, Query

from app.api.dependencies import Service
from app.api.schemas import ApiResponse, CourseInput, EnrollmentInput, UserInput
from app.domain.entities import Course, Enrollment, User, UserCourses

router = APIRouter()
Identifier = Annotated[int, Path(gt=0)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


def response(message, data=None):
    return {"success": True, "message": message, "data": data}


@router.post("/users", status_code=201, response_model=ApiResponse[User], tags=["Users"])
def create_user(payload: UserInput, service: Service):
    return response("User created", service.create_user(**payload.model_dump()))


@router.get("/users", response_model=ApiResponse[list[User]], tags=["Users"])
def list_users(service: Service, offset: Offset = 0, limit: Limit = 100):
    return response("Users retrieved", service.list_users(offset, limit))


@router.get("/users/{id}", response_model=ApiResponse[User], tags=["Users"])
def get_user(id: Identifier, service: Service):
    return response("User retrieved", service.get_user(id))


@router.put("/users/{id}", response_model=ApiResponse[User], tags=["Users"])
def update_user(id: Identifier, payload: UserInput, service: Service):
    return response("User updated", service.update_user(id, **payload.model_dump()))


@router.delete("/users/{id}", response_model=ApiResponse[None], tags=["Users"])
def delete_user(id: Identifier, service: Service):
    service.delete_user(id)
    return response("User deleted")


@router.post("/courses", status_code=201, response_model=ApiResponse[Course], tags=["Courses"])
def create_course(payload: CourseInput, service: Service):
    return response("Course created", service.create_course(**payload.model_dump()))


@router.get("/courses", response_model=ApiResponse[list[Course]], tags=["Courses"])
def list_courses(service: Service, offset: Offset = 0, limit: Limit = 100):
    return response("Courses retrieved", service.list_courses(offset, limit))


@router.get("/courses/{id}", response_model=ApiResponse[Course], tags=["Courses"])
def get_course(id: Identifier, service: Service):
    return response("Course retrieved", service.get_course(id))


@router.put("/courses/{id}", response_model=ApiResponse[Course], tags=["Courses"])
def update_course(id: Identifier, payload: CourseInput, service: Service):
    return response("Course updated", service.update_course(id, **payload.model_dump()))


@router.delete("/courses/{id}", response_model=ApiResponse[None], tags=["Courses"])
def delete_course(id: Identifier, service: Service):
    service.delete_course(id)
    return response("Course deleted")


@router.post("/enrollments", status_code=201, response_model=ApiResponse[Enrollment], tags=["Enrollments"])
def enroll(payload: EnrollmentInput, service: Service):
    return response("Enrollment created", service.enroll(**payload.model_dump()))


@router.get("/users/{id}/courses", response_model=ApiResponse[UserCourses], tags=["Enrollments"])
def user_courses(id: Identifier, service: Service):
    return response("User courses retrieved", service.user_courses(id))
