from __future__ import annotations


def test_generated_output_type_validation_returns_standard_validation_error(client) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "invalid-type@example.com", "password": "supersecret123"},
    )
    _user_id = register_response.json()["id"]
    login_response = client.post(
        "/api/auth/login",
        json={"email": "invalid-type@example.com", "password": "supersecret123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/applications/app-1/generated-outputs",
        params={"type": "bad_type"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"
