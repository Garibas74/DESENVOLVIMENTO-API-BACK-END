from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Data = TypeVar("Data")


class ApiResponse(BaseModel, Generic[Data]):
    success: bool = True
    message: str
    data: Data | None = None


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class UserInput(InputModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=254)


class CourseInput(InputModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    workload: int = Field(gt=0, strict=True)


class EnrollmentInput(InputModel):
    user_id: int = Field(gt=0, strict=True)
    course_id: int = Field(gt=0, strict=True)
