from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime


@dataclass
class Course:
    id: int
    title: str
    description: str
    workload: int


@dataclass
class Enrollment:
    id: int
    user_id: int
    course_id: int
    enrolled_at: datetime


@dataclass
class UserCourses:
    user: User
    courses: list[Course]
