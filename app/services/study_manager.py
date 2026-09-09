from app.domain.errors import ConflictError, NotFoundError
from app.domain.repositories import CourseRepository, EnrollmentRepository, UserRepository


class StudyManager:
    def __init__(self, users: UserRepository, courses: CourseRepository,
                 enrollments: EnrollmentRepository):
        self.users = users
        self.courses = courses
        self.enrollments = enrollments

    def get_user(self, user_id: int):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def list_users(self, offset: int, limit: int):
        return self.users.list(offset, limit)

    def _check_email(self, email: str, user_id: int | None = None):
        existing = self.users.find(email=email)
        if existing is not None and existing.id != user_id:
            raise ConflictError("Email already registered")

    def create_user(self, name: str, email: str):
        email = email.strip().lower()
        self._check_email(email)
        return self.users.create(name=name, email=email)

    def update_user(self, user_id: int, name: str, email: str):
        self.get_user(user_id)
        email = email.strip().lower()
        self._check_email(email, user_id)
        return self.users.update(user_id, name=name, email=email)

    def delete_user(self, user_id: int):
        self.get_user(user_id)
        self.users.delete(user_id)

    def get_course(self, course_id: int):
        course = self.courses.get(course_id)
        if course is None:
            raise NotFoundError("Course not found")
        return course

    def list_courses(self, offset: int, limit: int):
        return self.courses.list(offset, limit)

    def create_course(self, title: str, description: str, workload: int):
        return self.courses.create(title=title, description=description, workload=workload)

    def update_course(self, course_id: int, title: str, description: str, workload: int):
        self.get_course(course_id)
        return self.courses.update(course_id, title=title, description=description, workload=workload)

    def delete_course(self, course_id: int):
        self.get_course(course_id)
        self.courses.delete(course_id)

    def enroll(self, user_id: int, course_id: int):
        self.get_user(user_id)
        self.get_course(course_id)
        if self.enrollments.find(user_id=user_id, course_id=course_id):
            raise ConflictError("User already enrolled in this course")
        return self.enrollments.create(user_id=user_id, course_id=course_id)

    def user_courses(self, user_id: int):
        result = self.users.with_courses(user_id)
        if result is None:
            raise NotFoundError("User not found")
        return result
