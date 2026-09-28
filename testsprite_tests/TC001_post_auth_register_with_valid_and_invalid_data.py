import requests
import uuid
import sys
import traceback

BASE_URL = "http://localhost:3000"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
TIMEOUT = 30


def test_auth_register_valid_and_invalid_data():
    created_user_id = None
    unique_email = f"testuser_{uuid.uuid4().hex}@example.com"

    try:
        # 1) Successful registration with valid data
        valid_payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password": "Password123@",
            "confirm_password": "Password123@"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=valid_payload, headers=HEADERS, timeout=TIMEOUT)
        try:
            body = resp.json()
        except Exception:
            body = None

        assert resp.status_code in (200, 201), f"Expected HTTP 200/201 for successful registration, got {resp.status_code}, body={body}"
        assert isinstance(body, dict), f"Response body is not JSON object for successful registration: {body}"
        assert body.get("statusCode") == 201, f"Expected wrapper.statusCode==201, got {body.get('statusCode')}, body={body}"
        assert body.get("success") is True, f"Expected wrapper.success==True for successful registration, got {body.get('success')}, body={body}"
        data = body.get("data")
        assert isinstance(data, dict), f"Expected wrapper.data to be an object, got: {data}"
        # Confirm returned data contains email and does not contain password
        assert data.get("email") == unique_email, f"Registered email mismatch. expected={unique_email}, got={data.get('email')}"
        assert "password" not in data, f"Password should not be returned in response data, but found: {data}"
        # Attempt to capture user id for cleanup (may vary by implementation)
        created_user_id = data.get("id") or data.get("user_id") or None

        # 2) Conflict error when email already exists
        resp_conflict = requests.post(f"{BASE_URL}/auth/register", json=valid_payload, headers=HEADERS, timeout=TIMEOUT)
        try:
            body_conflict = resp_conflict.json()
        except Exception:
            body_conflict = None

        # Expecting 409 Conflict; server uses wrapper.statusCode
        assert resp_conflict.status_code in (400, 409, 422), f"Expected HTTP 409/400/422 for duplicate registration, got {resp_conflict.status_code}, body={body_conflict}"
        assert isinstance(body_conflict, dict), f"Conflict response not JSON: {body_conflict}"
        # Prefer checking wrapper.statusCode if present
        if "statusCode" in body_conflict:
            assert body_conflict.get("statusCode") == 409, f"Expected wrapper.statusCode==409 for duplicate email, got {body_conflict.get('statusCode')}, body={body_conflict}"
        assert body_conflict.get("success") is False, f"Expected wrapper.success==False for duplicate registration, got {body_conflict.get('success')}, body={body_conflict}"

        # 3) Validation error with invalid email
        invalid_email_payload = {
            "first_name": "Invalid",
            "last_name": "Email",
            "email": "invalid-email",
            "password": "Password123@",
            "confirm_password": "Password123@"
        }
        resp_invalid_email = requests.post(f"{BASE_URL}/auth/register", json=invalid_email_payload, headers=HEADERS, timeout=TIMEOUT)
        try:
            body_invalid_email = resp_invalid_email.json()
        except Exception:
            body_invalid_email = None

        assert resp_invalid_email.status_code in (400, 422), f"Expected HTTP 400/422 for invalid email, got {resp_invalid_email.status_code}, body={body_invalid_email}"
        assert isinstance(body_invalid_email, dict), f"Invalid email response not JSON: {body_invalid_email}"
        assert body_invalid_email.get("success") is False, f"Expected wrapper.success==False for invalid email, got {body_invalid_email.get('success')}, body={body_invalid_email}"
        if "statusCode" in body_invalid_email:
            assert body_invalid_email.get("statusCode") == 400 or body_invalid_email.get("statusCode") == 422, f"Expected wrapper.statusCode 400/422 for invalid email, got {body_invalid_email.get('statusCode')}"

        # 4) Validation error with mismatched confirm_password
        mismatch_payload = {
            "first_name": "Mismatch",
            "last_name": "Password",
            "email": f"mismatch_{uuid.uuid4().hex}@example.com",
            "password": "Password123@",
            "confirm_password": "DifferentPassword!"
        }
        resp_mismatch = requests.post(f"{BASE_URL}/auth/register", json=mismatch_payload, headers=HEADERS, timeout=TIMEOUT)
        try:
            body_mismatch = resp_mismatch.json()
        except Exception:
            body_mismatch = None

        assert resp_mismatch.status_code in (400, 422), f"Expected HTTP 400/422 for mismatched passwords, got {resp_mismatch.status_code}, body={body_mismatch}"
        assert isinstance(body_mismatch, dict), f"Mismatched password response not JSON: {body_mismatch}"
        assert body_mismatch.get("success") is False, f"Expected wrapper.success==False for mismatched confirm_password, got {body_mismatch.get('success')}, body={body_mismatch}"
        if "statusCode" in body_mismatch:
            assert body_mismatch.get("statusCode") == 400 or body_mismatch.get("statusCode") == 422, f"Expected wrapper.statusCode 400/422 for mismatched confirm_password, got {body_mismatch.get('statusCode')}"

    except Exception as exc:
        # Re-raise after printing traceback for easier debugging when running tests
        traceback.print_exc()
        raise

    finally:
        # Cleanup: attempt to delete the created user if we have an id
        if created_user_id:
            try:
                delete_resp = requests.delete(f"{BASE_URL}/employees/{created_user_id}", headers=HEADERS, timeout=TIMEOUT)
                # Deletion may require admin privileges; do not fail the test if deletion is unauthorized.
                if delete_resp.status_code not in (200, 204):
                    # Attempt best-effort alternative: maybe delete by email via admin-less endpoint is not available.
                    pass
            except Exception:
                # Ignore cleanup failures, but do not suppress the main test result
                pass


if __name__ == "__main__":
    try:
        test_auth_register_valid_and_invalid_data()
        print("TC001: PASS")
        sys.exit(0)
    except AssertionError as e:
        print("TC001: FAIL - AssertionError:", str(e))
        sys.exit(1)
    except Exception as e:
        print("TC001: ERROR - Exception:", str(e))
        sys.exit(2)