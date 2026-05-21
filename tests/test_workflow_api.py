from __future__ import annotations


def _auth_headers(client) -> tuple[str, dict[str, str]]:
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "workflow@example.com", "password": "supersecret123"},
    )
    user_id = register_response.json()["id"]
    login_response = client.post(
        "/api/auth/login",
        json={"email": "workflow@example.com", "password": "supersecret123"},
    )
    token = login_response.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


def test_agent_run_generates_steps_and_outputs(client, db_session) -> None:
    _user_id, headers = _auth_headers(client)

    from careerpilot.models.resume import Resume

    resume = Resume(
        id="resume-wf-1",
        user_id="ignored-until-updated",
        file_name="resume.pdf",
        raw_text="Ada Lovelace\nPython\nProject: agent workflow platform",
        parsed_json={
            "basic_info": {"name": "Ada Lovelace", "email": "", "phone": "", "location": ""},
            "education": [],
            "skills": ["Python", "LangGraph"],
            "projects": ["agent workflow platform"],
            "experience": ["internship experience"],
            "awards": [],
        },
        embedding_text="resume text",
        embedding_metadata={"source_type": "resume"},
    )
    from careerpilot.models.auth import User

    user = db_session.query(User).filter(User.email == "workflow@example.com").one()
    resume.user_id = user.id
    db_session.add(resume)
    db_session.commit()

    application_response = client.post(
        "/api/applications",
        headers=headers,
        json={
            "resume_id": "resume-wf-1",
            "company_name": "ByteDance",
            "job_title": "AI Agent Developer Intern",
            "job_description": "Need Python, LangGraph, LLM workflow design.",
        },
    )
    application_id = application_response.json()["id"]

    run_response = client.post(
        "/api/agent-runs",
        headers=headers,
        json={"application_id": application_id, "workflow_type": "full_application"},
    )

    assert run_response.status_code == 200
    run_id = run_response.json()["run_id"]
    assert run_response.json()["status"] == "success"

    steps_response = client.get(f"/api/agent-runs/{run_id}/steps", headers=headers)
    assert steps_response.status_code == 200
    steps = steps_response.json()["steps"]
    assert len(steps) == 8
    assert steps[-1]["agent_name"] == "EvaluationAgent"

    generated_response = client.get(
        f"/api/applications/{application_id}/generated-outputs",
        headers=headers,
        params={"type": "evaluation"},
    )
    assert generated_response.status_code == 200
    assert generated_response.json()["output_type"] == "evaluation"
    assert "citations" in generated_response.json()["metadata"]
