from __future__ import annotations


def _auth_headers(client, suffix: str = "company") -> tuple[str, dict[str, str]]:
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Ada",
            "email": f"{suffix}@example.com",
            "password": "supersecret123",
        },
    )
    user_id = register_response.json()["id"]
    login_response = client.post(
        "/api/auth/login",
        json={"email": f"{suffix}@example.com", "password": "supersecret123"},
    )
    token = login_response.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def test_application_can_store_company_context(client, db_session) -> None:
    user_id, headers = _auth_headers(client, "company-profile")

    from careerpilot.models.resume import Resume

    resume = Resume(
        id="resume-company-1",
        user_id=user_id,
        file_name="resume.pdf",
        raw_text="Ada Lovelace\nPython\nProject Alpha",
        parsed_json={
            "basic_info": {"name": "Ada Lovelace", "email": "", "phone": "", "location": ""},
            "education": [],
            "skills": ["Python", "FastAPI"],
            "projects": ["Project Alpha"],
            "experience": ["Internship at Lab"],
            "awards": [],
        },
        embedding_text="resume text",
        embedding_metadata={"source_type": "resume"},
    )
    db_session.add(resume)
    db_session.commit()

    create_response = client.post(
        "/api/applications",
        headers=headers,
        json={
            "resume_id": "resume-company-1",
            "company_name": "OpenAI",
            "job_title": "AI Engineer",
            "job_description": "Need Python and agent workflow design.",
            "company_context": (
                "OpenAI builds production AI systems, APIs, safety processes, "
                "and evaluation infrastructure."
            ),
        },
    )

    assert create_response.status_code == 201
    application_id = create_response.json()["id"]
    assert create_response.json()["has_company_context"] is True

    company_profile_response = client.get(
        f"/api/applications/{application_id}/company-profile",
        headers=headers,
    )

    assert company_profile_response.status_code == 200
    assert company_profile_response.json()["company_name"] == "OpenAI"
    assert "evaluation infrastructure" in company_profile_response.json()["content"]
