from typing import Protocol, TypeVar

from app.domain.entities import Course, Enrollment, User, UserCourses

Entity = TypeVar("Entity")


class Repository(Protocol[Entity]):
    def get(self, entity_id: int) -> Entity | None: ...
    def list(self, offset: int, limit: int) -> list[Entity]: ...
    def find(self, **filters) -> Entity | None: ...
    def create(self, **values) -> Entity: ...
    def update(self, entity_id: int, **values) -> Entity: ...
    def delete(self, entity_id: int) -> None: ...


class UserRepository(Repository[User], Protocol):
    def with_courses(self, user_id: int) -> UserCourses | None: ...


class CourseRepository(Repository[Course], Protocol):
    pass


class EnrollmentRepository(Repository[Enrollment], Protocol):
    pass
