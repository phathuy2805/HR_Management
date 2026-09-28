import requests
import datetime
import uuid
import sys

BASE_URL = "http://localhost:3000"
TIMEOUT = 30


def test_TC009_post_leave_requests_with_valid_and_invalid_data():
    session = requests.Session()

    # Create unique test user and authenticate to obtain Bearer token
    unique_suffix = str(uuid.uuid4())[:8]
    test_email = f"test.user.{unique_suffix}@example.com"
    password = "Password123@"

    register_payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": test_email,
        "password": password,
        "confirm_password": password
    }

    try:
        # Register
        r = session.post(f"{BASE_URL}/auth/register", json=register_payload, timeout=TIMEOUT)
        try:
            r_json = r.json()
        except ValueError:
            raise AssertionError(f"Register: expected JSON response, got status {r.status_code}, body: {r.text}")

        assert r.status_code in (200, 201), f"Register failed HTTP status: {r.status_code}, body: {r.text}"
        assert isinstance(r_json, dict), "Register response is not a JSON object"
        # TransformInterceptor wrapper expected
        assert "success" in r_json and "statusCode" in r_json and "data" in r_json, f"Register response wrapper missing keys: {r_json}"

        # Login
        login_payload = {"email": test_email, "password": password}
        r = session.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=TIMEOUT)
        try:
            login_json = r.json()
        except ValueError:
            raise AssertionError(f"Login: expected JSON response, got status {r.status_code}, body: {r.text}")

        assert r.status_code == login_json.get("statusCode", r.status_code), "Login HTTP status does not match wrapper statusCode"
        assert login_json.get("statusCode") == 201, f"Login expected statusCode 201, got {login_json.get('statusCode')}, body: {login_json}"
        access_token = None
        if isinstance(login_json.get("data"), dict):
            access_token = login_json["data"].get("access_token")
        assert access_token, f"Login did not return access_token: {login_json}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        created_leave_id = None

        # 1) Valid leave request: start_date < end_date, valid type -> expect 201 with PENDING
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=2)
        valid_payload = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "type": "VACATION",
            "reason": "Family trip"
        }

        r = session.post(f"{BASE_URL}/leave-requests", json=valid_payload, headers=headers, timeout=TIMEOUT)
        try:
            resp = r.json()
        except ValueError:
            raise AssertionError(f"Valid leave request: expected JSON response, got status {r.status_code}, body: {r.text}")

        # Validate wrapper and HTTP code
        assert r.status_code == resp.get("statusCode", r.status_code), f"Valid leave HTTP status mismatch: {r.status_code} vs wrapper {resp.get('statusCode')}"
        assert resp.get("statusCode") == 201, f"Valid leave expected statusCode 201, got {resp.get('statusCode')}, body: {resp}"
        assert resp.get("success") is True, f"Valid leave expected success true, got: {resp}"

        # Validate created data contains id and status PENDING
        data = resp.get("data")
        assert isinstance(data, dict), f"Valid leave response data is not object: {data}"
        created_leave_id = data.get("id") or data.get("_id") or data.get("leave_request_id")
        assert created_leave_id, f"Valid leave response missing id: {data}"
        status = data.get("status") or data.get("state")
        # If API returns status, expect PENDING. If not present, skip strict assert.
        if status is not None:
            assert status.upper() == "PENDING", f"Expected leave status PENDING, got {status}"

        # 2) Invalid leave request: end_date before start_date -> expect 400
        invalid_range_payload = {
            "start_date": start_date.isoformat(),
            "end_date": (start_date - datetime.timedelta(days=1)).isoformat(),
            "type": "SICK",
            "reason": "Invalid range test"
        }

        r = session.post(f"{BASE_URL}/leave-requests", json=invalid_range_payload, headers=headers, timeout=TIMEOUT)
        try:
            resp_invalid = r.json()
        except ValueError:
            raise AssertionError(f"Invalid range: expected JSON response, got status {r.status_code}, body: {r.text}")

        assert r.status_code == resp_invalid.get("statusCode", r.status_code), f"Invalid range HTTP status mismatch: {r.status_code} vs wrapper {resp_invalid.get('statusCode')}"
        assert resp_invalid.get("statusCode") == 400, f"Invalid range expected statusCode 400, got {resp_invalid.get('statusCode')}, body: {resp_invalid}"

        # 3) Invalid leave request: missing required start_date -> expect 400
        missing_field_payload = {
            "end_date": end_date.isoformat(),
            "type": "CASUAL"
        }

        r = session.post(f"{BASE_URL}/leave-requests", json=missing_field_payload, headers=headers, timeout=TIMEOUT)
        try:
            resp_missing = r.json()
        except ValueError:
            raise AssertionError(f"Missing field: expected JSON response, got status {r.status_code}, body: {r.text}")

        assert r.status_code == resp_missing.get("statusCode", r.status_code), f"Missing field HTTP status mismatch: {r.status_code} vs wrapper {resp_missing.get('statusCode')}"
        assert resp_missing.get("statusCode") == 400, f"Missing field expected statusCode 400, got {resp_missing.get('statusCode')}, body: {resp_missing}"

    except requests.RequestException as e:
        raise AssertionError(f"HTTP request failed: {e}") from e
    finally:
        # Cleanup: delete created leave request if exists
        if 'created_leave_id' in locals() and created_leave_id:
            try:
                dr = session.delete(f"{BASE_URL}/leave-requests/{created_leave_id}", headers=headers, timeout=TIMEOUT)
                # If delete endpoint exists, expect 200 or 204 or wrapper with statusCode
                try:
                    dr_json = dr.json()
                    if isinstance(dr_json, dict) and "statusCode" in dr_json:
                        assert dr_json.get("statusCode") in (200, 204, 202), f"Unexpected delete wrapper statusCode: {dr_json}"
                except ValueError:
                    # Non-JSON delete response is acceptable as long as HTTP status is success
                    assert dr.status_code in (200, 202, 204, 404), f"Unexpected delete HTTP status: {dr.status_code}, body: {dr.text}"
            except requests.RequestException:
                # best-effort cleanup; do not mask original test results
                pass


if __name__ == "__main__":
    try:
        test_TC009_post_leave_requests_with_valid_and_invalid_data()
        print("TC009: PASSED")
    except AssertionError as e:
        print("TC009: FAILED -", str(e))
        sys.exit(1)
    except Exception as e:
        print("TC009: ERROR -", str(e))
        sys.exit(2)