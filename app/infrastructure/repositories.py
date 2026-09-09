from dataclasses import fields
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.domain.entities import Course, Enrollment, User, UserCourses
from app.domain.errors import ConflictError, NotFoundError
from app.infrastructure.models import CourseModel, EnrollmentModel, UserModel


def to_entity(model, entity_type):
    values = {field.name: getattr(model, field.name) for field in fields(entity_type)}
    for key, value in values.items():
        if isinstance(value, datetime) and value.tzinfo is None:
            values[key] = value.replace(tzinfo=timezone.utc)
    return entity_type(**values)


class SqlRepository:
    def __init__(self, session: Session, model, entity_type):
        self.session = session
        self.model = model
        self.entity_type = entity_type

    def get(self, entity_id):
        model = self.session.get(self.model, entity_id)
        return to_entity(model, self.entity_type) if model else None

    def list(self, offset, limit):
        query = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return [to_entity(row, self.entity_type) for row in self.session.scalars(query)]

    def find(self, **filters):
        model = self.session.scalar(select(self.model).filter_by(**filters))
        return to_entity(model, self.entity_type) if model else None

    def _commit(self):
        try:
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise ConflictError("Record conflicts with existing data or references") from error

    def create(self, **values):
        model = self.model(**values)
        self.session.add(model)
        self._commit()
        self.session.refresh(model)
        return to_entity(model, self.entity_type)

    def _require_model(self, entity_id):
        model = self.session.get(self.model, entity_id)
        if model is None:
            raise NotFoundError("Record not found")
        return model

    def update(self, entity_id, **values):
        model = self._require_model(entity_id)
        for key, value in values.items():
            setattr(model, key, value)
        self._commit()
        self.session.refresh(model)
        return to_entity(model, self.entity_type)

    def delete(self, entity_id):
        self.session.delete(self._require_model(entity_id))
        self._commit()


class SqlUserRepository(SqlRepository):
    def __init__(self, session):
        super().__init__(session, UserModel, User)

    def with_courses(self, user_id):
        query = select(UserModel).where(UserModel.id == user_id).options(
            selectinload(UserModel.enrollments).selectinload(EnrollmentModel.course))
        user = self.session.scalar(query)
        if user is None:
            return None
        return UserCourses(to_entity(user, User), [
            to_entity(enrollment.course, Course) for enrollment in user.enrollments])


class SqlCourseRepository(SqlRepository):
    def __init__(self, session):
        super().__init__(session, CourseModel, Course)


class SqlEnrollmentRepository(SqlRepository):
    def __init__(self, session):
        super().__init__(session, EnrollmentModel, Enrollment)
