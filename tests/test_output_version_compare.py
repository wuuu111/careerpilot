from __future__ import annotations

from datetime import timedelta

from careerpilot.utils import utcnow


def test_generated_output_history_and_compare_endpoints(client, db_session) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "history@example.com", "password": "supersecret123"},
    )
    user_id = register_response.json()["id"]
    login_response = client.post(
        "/api/auth/login",
        json={"email": "history@example.com", "password": "supersecret123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    from careerpilot.models.application import Application
    from careerpilot.models.generated_output import GeneratedOutput
    from careerpilot.models.job_description import JobDescription
    from careerpilot.models.resume import Resume

    resume = Resume(
        id="resume-history-1",
        user_id=user_id,
        file_name="resume.pdf",
        raw_text="raw",
        parsed_json={
            "basic_info": {"name": "Ada", "email": "", "phone": "", "location": ""},
            "education": [],
            "skills": ["Python"],
            "projects": ["Project Alpha"],
            "experience": [],
            "awards": [],
        },
        embedding_text="resume text",
        embedding_metadata={"source_type": "resume"},
    )
    job_description = JobDescription(
        id="jd-history-1",
        user_id=user_id,
        company_name="OpenAI",
        job_title="AI Engineer",
        raw_text="jd text",
        parsed_json={
            "role_type": "AI Engineer",
            "responsibilities": [],
            "required_skills": ["Python"],
            "preferred_skills": [],
            "keywords": ["Python"],
            "business_scenario": "",
            "seniority_level": "mid",
        },
        embedding_text="jd text",
        embedding_metadata={"source_type": "jd"},
    )
    application = Application(
        id="app-history-1",
        user_id=user_id,
        resume_id="resume-history-1",
        jd_id="jd-history-1",
        status="completed",
    )
    older = GeneratedOutput(
        application_id="app-history-1",
        output_type="matching_report",
        content='{"overall_score":70,"recommendations":["Add Python metrics"]}',
        output_metadata={"overall_score": 70, "citations": [{"source_type": "resume"}]},
        embedding_text="old output",
        embedding_metadata={"source_type": "generated_output"},
        created_at=utcnow() - timedelta(minutes=5),
    )
    newer = GeneratedOutput(
        application_id="app-history-1",
        output_type="matching_report",
        content='{"overall_score":82,"recommendations":["Highlight shipped systems"]}',
        output_metadata={"overall_score": 82, "citations": [{"source_type": "jd"}]},
        embedding_text="new output",
        embedding_metadata={"source_type": "generated_output"},
        created_at=utcnow(),
    )

    db_session.add_all([resume, job_description, application, older, newer])
    db_session.commit()

    history_response = client.get(
        "/api/applications/app-history-1/generated-outputs/history",
        params={"type": "matching_report"},
        headers=headers,
    )

    assert history_response.status_code == 200
    history = history_response.json()["items"]
    assert len(history) == 2
    assert history[0]["version"] == "v2"
    assert history[1]["version"] == "v1"

    compare_response = client.get(
        "/api/applications/app-history-1/generated-outputs/compare",
        params={"type": "matching_report"},
        headers=headers,
    )

    assert compare_response.status_code == 200
    body = compare_response.json()
    assert body["current"]["version"] == "v2"
    assert body["previous"]["version"] == "v1"
    assert "overall_score" in body["diff"]["changed_fields"]
