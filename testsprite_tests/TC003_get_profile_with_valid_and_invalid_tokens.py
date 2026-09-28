import requests
import uuid
import time
import sys

BASE_URL = "http://localhost:3000"
TIMEOUT = 30

def assert_status_and_wrapper(resp, expected_http_status):
    try:
        body = resp.json()
    except ValueError:
        body = None
    # HTTP status or wrapped statusCode should match expected
    if resp.status_code != expected_http_status:
        if not (body and isinstance(body, dict) and body.get("statusCode") == expected_http_status):
            raise AssertionError(f"Expected HTTP status {expected_http_status} or wrapper statusCode {expected_http_status}, got HTTP {resp.status_code}, body: {resp.text}")
    # If wrapper present, ensure structure
    if body and isinstance(body, dict):
        if "success" not in body or "statusCode" not in body or "timestamp" not in body:
            raise AssertionError(f"Response wrapper missing expected keys. Body: {body}")
    return body

def test_get_profile_with_valid_and_invalid_tokens():
    register_url = f"{BASE_URL}/auth/register"
    login_url = f"{BASE_URL}/auth/login"
    profile_url = f"{BASE_URL}/profile"

    password = "Password123@"
    unique_email = f"test_{int(time.time())}_{uuid.uuid4().hex[:6]}@example.com"
    register_payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": unique_email,
        "password": password,
        "confirm_password": password
    }

    created_user_data = None
    access_token = None

    try:
        # 1) Register a new user
        try:
            r = requests.post(register_url, json=register_payload, timeout=TIMEOUT)
        except Exception as e:
            raise AssertionError(f"Register request failed: {e}")
        body = assert_status_and_wrapper(r, 201)
        created_user_data = body.get("data") if body else None

        # 2) Login to obtain access token
        login_payload = {"email": unique_email, "password": password}
        try:
            r = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
        except Exception as e:
            raise AssertionError(f"Login request failed: {e}")
        body = assert_status_and_wrapper(r, 201)
        if not body or "data" not in body or "access_token" not in body["data"]:
            raise AssertionError(f"Login response missing access_token. Body: {body}")
        access_token = body["data"]["access_token"]

        # 3) GET /profile with valid token -> expect 200
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            r = requests.get(profile_url, headers=headers, timeout=TIMEOUT)
        except Exception as e:
            raise AssertionError(f"Profile request (valid token) failed: {e}")
        body = assert_status_and_wrapper(r, 200)
        # Validate returned profile data contains expected email when available
        profile_data = body.get("data") if body else None
        if profile_data and isinstance(profile_data, dict):
            if "email" in profile_data:
                assert profile_data["email"] == unique_email, f"Profile email mismatch: expected {unique_email}, got {profile_data['email']}"

        # 4) GET /profile without token -> expect 401
        try:
            r = requests.get(profile_url, timeout=TIMEOUT)
        except Exception as e:
            raise AssertionError(f"Profile request (no token) failed: {e}")
        _ = assert_status_and_wrapper(r, 401)

        # 5) GET /profile with invalid token -> expect 401
        bad_headers = {"Authorization": "Bearer invalid.token.here"}
        try:
            r = requests.get(profile_url, headers=bad_headers, timeout=TIMEOUT)
        except Exception as e:
            raise AssertionError(f"Profile request (invalid token) failed: {e}")
        _ = assert_status_and_wrapper(r, 401)

    finally:
        # Attempt to clean up created user if possible.
        # Try to discover user id from register response and attempt DELETE /employees/:id
        if created_user_data and isinstance(created_user_data, dict):
            user_id = created_user_data.get("id") or created_user_data.get("user_id") or created_user_data.get("_id")
            if user_id:
                delete_url = f"{BASE_URL}/employees/{user_id}"
                headers = {}
                if access_token:
                    headers["Authorization"] = f"Bearer {access_token}"
                try:
                    # Attempt deletion; do not fail the test if cleanup is not permitted
                    requests.delete(delete_url, headers=headers, timeout=TIMEOUT)
                except Exception:
                    pass

if __name__ == "__main__":
    test_get_profile_with_valid_and_invalid_tokens()
    print("TC003 completed successfully.")