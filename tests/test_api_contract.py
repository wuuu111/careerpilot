from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_and_login_flow_returns_token(client) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "supersecret123"},
    )

    assert register_response.status_code == 201
    body = register_response.json()
    assert body["email"] == "ada@example.com"

    login_response = client.post(
        "/api/auth/login",
        json={"email": "ada@example.com", "password": "supersecret123"},
    )

    assert login_response.status_code == 200
    token_body = login_response.json()
    assert token_body["access_token"]
    assert token_body["token_type"] == "bearer"


def test_login_sets_auth_cookie_and_me_accepts_cookie_auth(client) -> None:
    client.post(
        "/api/auth/register",
        json={"name": "Cookie Ada", "email": "cookie@example.com", "password": "supersecret123"},
    )

    login_response = client.post(
        "/api/auth/login",
        json={"email": "cookie@example.com", "password": "supersecret123"},
    )

    assert login_response.status_code == 200
    set_cookie = login_response.headers.get("set-cookie", "")
    assert "careerpilot_session=" in set_cookie
    assert "HttpOnly" in set_cookie

    me_response = client.get("/api/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "cookie@example.com"

    csrf_token = login_response.cookies.get("careerpilot_csrf_token")
    assert csrf_token

    logout_response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})

    assert logout_response.status_code == 204

    me_after_logout = client.get("/api/auth/me")
    assert me_after_logout.status_code == 401


def test_cookie_session_requires_csrf_token_for_authenticated_mutations(client) -> None:
    client.post(
        "/api/auth/register",
        json={"name": "Csrf Ada", "email": "csrf@example.com", "password": "supersecret123"},
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "csrf@example.com", "password": "supersecret123"},
    )

    csrf_token = login_response.cookies.get("careerpilot_csrf_token")

    assert csrf_token

    missing_header_response = client.post("/api/auth/logout")

    assert missing_header_response.status_code == 403
    assert missing_header_response.json() == {
        "error_code": "CSRF_VALIDATION_FAILED",
        "message": "CSRF validation failed.",
        "details": {},
    }

    success_response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})

    assert success_response.status_code == 204


def test_login_cookie_secure_defaults_by_environment_and_is_configurable(
    db_session, monkeypatch
) -> None:
    from careerpilot.api.main import create_app
    from careerpilot.config import get_settings
    from careerpilot.db import get_db

    def login_with_current_settings(name: str, email: str):
        app = create_app()

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            test_client.post(
                "/api/auth/register",
                json={"name": name, "email": email, "password": "supersecret123"},
            )
            return test_client.post(
                "/api/auth/login",
                json={"email": email, "password": "supersecret123"},
            )

    monkeypatch.setenv("CAREERPILOT_ENVIRONMENT", "production")
    monkeypatch.delenv("CAREERPILOT_AUTH_COOKIE_SECURE", raising=False)
    get_settings.cache_clear()

    response = login_with_current_settings("Prod Ada", "prod@example.com")

    assert "Secure" in response.headers.get("set-cookie", "")

    monkeypatch.setenv("CAREERPILOT_AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()

    response = login_with_current_settings("Override Ada", "override@example.com")

    assert "Secure" not in response.headers.get("set-cookie", "")
    get_settings.cache_clear()


def test_cors_allows_localhost_dev_origins(client) -> None:
    response = client.options(
        "/api/auth/register",
        headers={
            "Origin": "http://127.0.0.1:4174",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-csrf-token",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4174"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "x-csrf-token" in response.headers["access-control-allow-headers"].lower()


def test_missing_generated_output_uses_standard_error_envelope(client, db_session) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada2@example.com", "password": "supersecret123"},
    )
    user_id = register_response.json()["id"]

    auth_response = client.post(
        "/api/auth/login",
        json={"email": "ada2@example.com", "password": "supersecret123"},
    )
    token = auth_response.json()["access_token"]

    from careerpilot.models.application import Application
    from careerpilot.models.job_description import JobDescription
    from careerpilot.models.resume import Resume

    resume = Resume(
        id="resume-1",
        user_id=user_id,
        file_name="resume.pdf",
        raw_text="raw",
        parsed_json={
            "basic_info": {},
            "education": [],
            "skills": [],
            "projects": [],
            "experience": [],
            "awards": [],
        },
        embedding_text="resume text",
        embedding_metadata={"source_type": "resume"},
    )
    job_description = JobDescription(
        id="jd-1",
        user_id=user_id,
        company_name="ByteDance",
        job_title="AI Agent Developer",
        raw_text="jd",
        parsed_json={
            "role_type": "AI Agent Developer",
            "responsibilities": [],
            "required_skills": [],
            "preferred_skills": [],
            "keywords": [],
            "business_scenario": "",
            "seniority_level": "intern",
        },
        embedding_text="jd text",
        embedding_metadata={"source_type": "jd"},
    )
    application = Application(
        id="app-1", user_id=user_id, resume_id="resume-1", jd_id="jd-1", status="completed"
    )

    db_session.add_all([resume, job_description, application])
    db_session.commit()

    response = client.get(
        "/api/applications/app-1/generated-outputs",
        params={"type": "evaluation"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "error_code": "GENERATED_OUTPUT_NOT_FOUND",
        "message": "No generated output found for type evaluation.",
        "details": {"application_id": "app-1", "output_type": "evaluation"},
    }
