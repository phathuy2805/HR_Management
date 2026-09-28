import os
import uuid
import requests
import time

BASE_URL = "http://localhost:3000"
TIMEOUT = 30


def test_get_employee_detail_by_id_role_access():
    # Helpers
    def random_email():
        return f"test.user.{uuid.uuid4().hex[:8]}@example.com"

    def parse_wrapper(resp):
        try:
            body = resp.json()
        except ValueError:
            body = None
        return body

    created_employee = None
    admin_token = None

    # Create a new regular employee via public registration
    register_payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": random_email(),
        "password": "Password123!",
        "confirm_password": "Password123!"
    }

    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise AssertionError(f"Failed to call /auth/register: {e}")

    body = parse_wrapper(r)
    # Validate wrapper structure and success
    assert body is not None, f"/auth/register did not return JSON. HTTP status: {r.status_code}"
    assert "success" in body and "statusCode" in body and "data" in body, f"Unexpected wrapper for /auth/register: {body}"
    assert body.get("success") is True and int(body.get("statusCode", 0)) in (200, 201), f"Registration failed: {body}"

    # Extract created employee id/email from response
    created_data = body.get("data") or {}
    # Some implementations return the created object directly, or nested under 'employee'; try both
    if not created_data:
        raise AssertionError(f"No data returned on registration: {body}")
    created_employee_id = created_data.get("id") or created_data.get("employee_id") or created_data.get("_id")
    created_employee_email = created_data.get("email") or register_payload["email"]
    if not created_employee_id:
        # Try common nesting
        if isinstance(created_data, dict):
            # Search for id in nested dicts
            for v in created_data.values():
                if isinstance(v, dict) and v.get("id"):
                    created_employee_id = v.get("id")
                    created_employee_email = v.get("email", created_employee_email)
                    break
    assert created_employee_id, f"Could not determine created employee id from registration response: {created_data}"
    created_employee = {"id": created_employee_id, "email": created_employee_email, "password": register_payload["password"]}

    # Login as the created regular user to obtain token
    login_payload = {"email": created_employee["email"], "password": created_employee["password"]}
    try:
        r = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise AssertionError(f"Failed to call /auth/login for created user: {e}")

    body = parse_wrapper(r)
    assert body is not None, f"/auth/login did not return JSON. HTTP status: {r.status_code}"
    # Expect login success (201) and tokens
    assert body.get("success") is True and int(body.get("statusCode", 0)) in (200, 201), f"Login failed for created user: {body}"
    tokens = (body.get("data") or {})
    access_token = tokens.get("access_token")
    assert access_token, f"No access_token returned on login: {body}"

    user_headers = {"Authorization": f"Bearer {access_token}"}

    # Attempt to GET /employees/:id with regular user token -> expect forbidden (403)
    try:
        r = requests.get(f"{BASE_URL}/employees/{created_employee['id']}", headers=user_headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise AssertionError(f"Failed to call GET /employees/:id as regular user: {e}")

    body = parse_wrapper(r)
    # Accept either HTTP 403 or wrapper statusCode 403 as indicator of forbidden access
    http_status = r.status_code
    wrapper_status = body.get("statusCode") if isinstance(body, dict) else None

    forbidden = (http_status == 403) or (wrapper_status == 403)
    assert forbidden, f"Regular user should be forbidden from GET /employees/:id but received HTTP {http_status} and body: {body}"

    # Optionally test allowed access with ADMIN or HR_MANAGER credentials from environment
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if admin_email and admin_password:
        try:
            r = requests.post(f"{BASE_URL}/auth/login", json={"email": admin_email, "password": admin_password}, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise AssertionError(f"Failed to call /auth/login for admin user: {e}")

        body = parse_wrapper(r)
        assert body is not None and body.get("success") is True and int(body.get("statusCode", 0)) in (200, 201), f"Admin login failed: {body}"
        admin_token = (body.get("data") or {}).get("access_token")
        assert admin_token, f"No access_token returned for admin login: {body}"

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        try:
            r = requests.get(f"{BASE_URL}/employees/{created_employee['id']}", headers=admin_headers, timeout=TIMEOUT)
        except requests.RequestException as e:
            raise AssertionError(f"Failed to call GET /employees/:id as admin: {e}")

        body = parse_wrapper(r)
        assert body is not None, f"GET /employees/:id as admin did not return JSON. HTTP status: {r.status_code}"
        # Expect success true and statusCode 200 and data containing the employee info
        assert body.get("success") is True, f"Admin request reported failure: {body}"
        assert int(body.get("statusCode", 0)) == 200, f"Expected statusCode 200 for admin GET /employees/:id but got: {body}"
        data = body.get("data")
        assert isinstance(data, dict), f"Expected data object for employee detail, got: {data}"
        # Validate that returned employee matches created employee id/email if present
        returned_id = data.get("id") or data.get("_id") or data.get("employee_id")
        returned_email = data.get("email")
        assert str(returned_id) == str(created_employee["id"]), f"Returned employee id mismatch. Expected {created_employee['id']}, got {returned_id}"
        if returned_email:
            assert returned_email == created_employee["email"], f"Returned employee email mismatch. Expected {created_employee['email']}, got {returned_email}"
    else:
        # Admin creds not provided; make test aware but do not fail the test because role-based allowed path couldn't be executed
        # Still consider the core check (regular user forbidden) as the primary verification for access control enforcement.
        print("ADMIN_EMAIL and ADMIN_PASSWORD not provided; skipping admin/HR_MANAGER allowed-access check.")

    # Cleanup: if admin token available, delete the created employee
    if admin_token:
        try:
            r = requests.delete(f"{BASE_URL}/employees/{created_employee['id']}", headers={"Authorization": f"Bearer {admin_token}"}, timeout=TIMEOUT)
            # Expect 200 with wrapper indicating success or statusCode 200
            body = parse_wrapper(r)
            if body and isinstance(body, dict):
                assert int(body.get("statusCode", 0)) in (200, 204), f"Unexpected statusCode on delete: {body}"
            else:
                assert r.status_code in (200, 204), f"Unexpected HTTP status on delete: {r.status_code}"
        except requests.RequestException as e:
            raise AssertionError(f"Failed to delete created employee during cleanup: {e}")
    else:
        # Cannot delete without admin privileges; print a reminder
        print("No admin token available; created employee was not deleted. Please clean up manually if required.")


if __name__ == "__main__":
    test_get_employee_detail_by_id_role_access()