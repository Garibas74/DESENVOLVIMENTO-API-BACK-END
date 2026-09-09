import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import get_service
from app.infrastructure.models import EnrollmentModel, UserModel
from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app("sqlite://")) as test_client:
        yield test_client


def user(client, email="ana@example.com"):
    result = client.post("/users", json={"name": "Ana", "email": email})
    assert result.status_code == 201
    return result.json()["data"]


def course(client):
    result = client.post("/courses", json={
        "title": "Python", "description": "Introdução a APIs", "workload": 40})
    assert result.status_code == 201
    return result.json()["data"]


def assert_error(result, status):
    assert result.status_code == status
    body = result.json()
    assert body["success"] is False
    assert body["data"] is None
    assert isinstance(body["message"], str)
    assert set(body) == {"success", "message", "data"}


def test_user_crud(client):
    created = user(client)
    assert created["created_at"].endswith("Z")
    assert client.get("/users").json()["data"] == [created]
    assert client.get("/users/1").json()["data"] == created
    updated = client.put("/users/1", json={"name": "  Ana Maria  ", "email": "ANA@example.com"})
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Ana Maria"
    assert updated.json()["data"]["email"] == "ana@example.com"
    assert client.delete("/users/1").json() == {
        "success": True, "message": "User deleted", "data": None}
    assert_error(client.get("/users/1"), 404)


def test_course_crud(client):
    created = course(client)
    assert client.get("/courses").json()["data"] == [created]
    assert client.get("/courses/1").json()["data"] == created
    updated = client.put("/courses/1", json={
        "title": "SQL", "description": "Banco de dados", "workload": 60})
    assert updated.status_code == 200
    assert updated.json()["data"]["workload"] == 60
    assert client.delete("/courses/1").status_code == 200
    assert_error(client.get("/courses/1"), 404)


def test_email_conflicts_and_rollback(client):
    user(client)
    assert_error(client.post("/users", json={"name": "Outra", "email": "ANA@example.com"}), 409)
    user(client, "bia@example.com")
    assert_error(client.put("/users/2", json={"name": "Bia", "email": "ana@example.com"}), 409)
    assert client.get("/users/2").json()["data"]["email"] == "bia@example.com"


def test_enrollment_and_relationship(client):
    first = user(client)
    second = user(client, "bia@example.com")
    first_course = course(client)
    second_course = course(client)
    assert client.get("/users/1/courses").json()["data"] == {"user": first, "courses": []}
    for course_id in [first_course["id"], second_course["id"]]:
        result = client.post("/enrollments", json={"user_id": first["id"], "course_id": course_id})
        assert result.status_code == 201
        assert result.json()["data"]["enrolled_at"].endswith("Z")
    assert_error(client.post("/enrollments", json={"user_id": 1, "course_id": 1}), 409)
    assert client.get("/users/1/courses").json()["data"] == {
        "user": first, "courses": [first_course, second_course]}
    assert client.get("/users/2/courses").json()["data"] == {"user": second, "courses": []}


@pytest.mark.parametrize("payload", [{"user_id": 9, "course_id": 1}, {"user_id": 1, "course_id": 9}])
def test_missing_enrollment_reference(client, payload):
    user(client)
    course(client)
    assert_error(client.post("/enrollments", json=payload), 404)


@pytest.mark.parametrize("resource", ["users", "courses"])
def test_cascade(client, resource):
    user(client)
    course(client)
    client.post("/enrollments", json={"user_id": 1, "course_id": 1})
    assert client.delete(f"/{resource}/1").status_code == 200
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(EnrollmentModel)) == 0
    other = "courses" if resource == "users" else "users"
    assert client.get(f"/{other}/1").status_code == 200


@pytest.mark.parametrize("path,payload", [
    ("/users", {}), ("/users", {"name": " ", "email": "ana@example.com"}),
    ("/users", {"name": "Ana", "email": "invalid"}),
    ("/users", {"name": "Ana", "email": "ana@example.com", "id": 1}),
    ("/courses", {"title": "Python", "description": "API", "workload": 0}),
    ("/courses", {"title": "Python", "description": "API", "workload": -1}),
    ("/courses", {"title": "Python", "description": "API", "workload": 1.5}),
    ("/courses", {"title": "Python", "description": "API", "workload": True}),
    ("/courses", {"title": " ", "description": "API", "workload": 10}),
    ("/enrollments", {"user_id": 0, "course_id": 1}),
])
def test_validation(client, path, payload):
    assert_error(client.post(path, json=payload), 422)


@pytest.mark.parametrize("path", ["/users/999", "/courses/999", "/users/999/courses"])
def test_missing_get(client, path):
    assert_error(client.get(path), 404)


@pytest.mark.parametrize("resource,payload", [
    ("users", {"name": "Ana", "email": "ana@example.com"}),
    ("courses", {"title": "Python", "description": "API", "workload": 40}),
])
def test_missing_mutations(client, resource, payload):
    assert_error(client.put(f"/{resource}/999", json=payload), 404)
    assert_error(client.delete(f"/{resource}/999"), 404)


def test_pagination_and_protocol_errors(client):
    user(client)
    user(client, "bia@example.com")
    assert len(client.get("/users?limit=1").json()["data"]) == 1
    assert client.get("/users?offset=1&limit=1").json()["data"][0]["id"] == 2
    for path in ["/users?limit=101", "/users?offset=-1", "/users/0", "/users/abc"]:
        assert_error(client.get(path), 422)
    assert_error(client.get("/unknown"), 404)
    assert_error(client.patch("/users/1", json={}), 405)
    assert_error(client.post("/users", content="{", headers={"Content-Type": "application/json"}), 422)


def test_database_constraints(client):
    user(client)
    course(client)
    with client.app.state.session_factory() as session:
        session.add(UserModel(name="Other", email="ana@example.com"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add(EnrollmentModel(user_id=999, course_id=1))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.add_all([EnrollmentModel(user_id=1, course_id=1), EnrollmentModel(user_id=1, course_id=1)])
        with pytest.raises(IntegrityError):
            session.commit()


def test_internal_error_is_sanitized(client):
    def broken_service():
        raise RuntimeError("secret database details")
    client.app.dependency_overrides[get_service] = broken_service
    with TestClient(client.app, raise_server_exceptions=False) as safe_client:
        result = safe_client.get("/users")
    assert_error(result, 500)
    assert result.json()["message"] == "Internal server error"


def test_openapi(client):
    schema = client.get("/openapi.json").json()
    assert len(schema["paths"]) == 6
    assert schema["paths"]["/enrollments"]["post"]["responses"]["201"]
