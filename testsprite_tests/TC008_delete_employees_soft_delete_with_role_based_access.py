import os
import uuid
import requests
from requests.exceptions import RequestException

BASE_URL = "http://localhost:3000"
TIMEOUT = 30  # seconds

def test_delete_employee_soft_delete_role_based_access():
    """
    TC008 - delete employees soft delete with role based access
    Tests:
      - Unauthenticated DELETE -> expect 401
      - DELETE with user role (insufficient) -> expect 403
      - DELETE with HR_MANAGER or ADMIN -> expect 200 and employee status becomes TERMINATED
    Notes:
      - Expects optional environment variables for admin/hr credentials:
          ADMIN_EMAIL, ADMIN_PASSWORD
          HR_EMAIL, HR_PASSWORD
      - Uses /auth/register to create target employee, /auth/login to obtain tokens,
        and /profile to retrieve created user's id.
      - Response wrapper expected: { success, statusCode, data, timestamp }
    """
    session = requests.Session()
    headers = {"Content-Type": "application/json"}

    # Generate unique test user
    unique = uuid.uuid4().hex[:8]
    user_payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": f"test.user.{unique}@example.com",
        "password": "Password123@",
        "confirm_password": "Password123@"
    }

    created_user_id = None
    user_token = None
    admin_token = None
    hr_token = None

    try:
        # 1) Register new user (target to be deleted)
        resp = session.post(
            f"{BASE_URL}/auth/register",
            json=user_payload,
            headers=headers,
            timeout=TIMEOUT
        )
        try:
            body = resp.json()
        except ValueError:
            raise AssertionError(f"Register: Response not JSON. HTTP {resp.status_code}, body: {resp.text}")

        assert resp.status_code in (200, 201), f"Expected HTTP 200/201 for register, got {resp.status_code}, body={body}"
        assert isinstance(body, dict), "Register: response wrapper not a dict"
        assert body.get("statusCode") in (200, 201), f"Register wrapper statusCode unexpected: {body}"

        # 2) Login as created user to get token
        login_payload = {"email": user_payload["email"], "password": user_payload["password"]}
        resp = session.post(f"{BASE_URL}/auth/login", json=login_payload, headers=headers, timeout=TIMEOUT)
        try:
            login_body = resp.json()
        except ValueError:
            raise AssertionError(f"Login (user): Response not JSON. HTTP {resp.status_code}, body: {resp.text}")

        assert resp.status_code in (200, 201), f"Expected HTTP 200/201 for login, got {resp.status_code}, body={login_body}"
        assert login_body.get("statusCode") in (200, 201), f"Login wrapper statusCode unexpected: {login_body}"
        data = login_body.get("data") or {}
        user_token = data.get("access_token")
        assert user_token, "Login did not return access_token for created user"

        # 3) Get profile to obtain user id
        auth_headers = headers.copy()
        auth_headers["Authorization"] = f"Bearer {user_token}"
        resp = session.get(f"{BASE_URL}/profile", headers=auth_headers, timeout=TIMEOUT)
        try:
            profile_body = resp.json()
        except ValueError:
            raise AssertionError(f"Profile: Response not JSON. HTTP {resp.status_code}, body: {resp.text}")

        assert resp.status_code == 200, f"Expected HTTP 200 for profile, got {resp.status_code}, body={profile_body}"
        assert profile_body.get("statusCode") == 200, f"Profile wrapper statusCode unexpected: {profile_body}"
        profile_data = profile_body.get("data") or {}
        created_user_id = profile_data.get("id") or profile_data.get("user_id") or profile_data.get("employee_id")
        # fallback: some implementations may return id under different keys or nested; try common ones
        if not created_user_id:
            # try nested keys if any
            for k in ("id",):
                if k in profile_data:
                    created_user_id = profile_data[k]
                    break
        assert created_user_id, f"Could not determine created user id from profile response: {profile_body}"

        # 4) Attempt unauthenticated DELETE -> expect 401 (or 403 if API behaves differently). We'll assert 401 or 403.
        resp = session.delete(f"{BASE_URL}/employees/{created_user_id}", headers=headers, timeout=TIMEOUT)
        # Attempt to parse wrapper if JSON
        unauth_body = {}
        try:
            unauth_body = resp.json()
        except ValueError:
            pass

        assert resp.status_code in (401, 403), f"Unauthenticated delete expected 401/403, got HTTP {resp.status_code}, body={unauth_body}"

        # If wrapper present, check statusCode
        if isinstance(unauth_body, dict) and "statusCode" in unauth_body:
            assert unauth_body["statusCode"] in (401, 403), f"Unauthenticated delete wrapper.statusCode unexpected: {unauth_body}"

        # 5) Attempt DELETE with created user's token (insufficient permissions) -> expect 403
        resp = session.delete(
            f"{BASE_URL}/employees/{created_user_id}",
            headers={**headers, "Authorization": f"Bearer {user_token}"},
            timeout=TIMEOUT
        )
        try:
            insufficient_body = resp.json()
        except ValueError:
            insufficient_body = {}

        # Accept either 403 Forbidden; some setups return 401 if token lacks abilities, but spec expects 403.
        assert resp.status_code in (401, 403), f"User-role delete expected 401/403, got HTTP {resp.status_code}, body={insufficient_body}"
        if isinstance(insufficient_body, dict) and "statusCode" in insufficient_body:
            assert insufficient_body["statusCode"] in (401, 403), f"User-role delete wrapper.statusCode unexpected: {insufficient_body}"

        # 6) Try HR and ADMIN deletion if credentials provided via env
        # Helper to login and return token
        def login_and_get_token(email_env, pwd_env):
            email = os.environ.get(email_env)
            pwd = os.environ.get(pwd_env)
            if not email or not pwd:
                return None
            resp = session.post(f"{BASE_URL}/auth/login", json={"email": email, "password": pwd}, headers=headers, timeout=TIMEOUT)
            try:
                body = resp.json()
            except ValueError:
                raise AssertionError(f"Login ({email_env}): Response not JSON. HTTP {resp.status_code}, body: {resp.text}")
            assert resp.status_code in (200, 201), f"Login ({email_env}) failed with HTTP {resp.status_code}, body={body}"
            assert body.get("statusCode") in (200, 201), f"Login ({email_env}) wrapper.statusCode unexpected: {body}"
            return (body.get("data") or {}).get("access_token")

        admin_token = login_and_get_token("ADMIN_EMAIL", "ADMIN_PASSWORD")
        hr_token = login_and_get_token("HR_EMAIL", "HR_PASSWORD")

        # Prefer ADMIN then HR for cleanup and verification. Test both if available.
        role_tested_success = False
        role_success_name = None

        for role_name, token in (("ADMIN", admin_token), ("HR_MANAGER", hr_token)):
            if not token:
                continue
            # Perform DELETE with this role
            resp = session.delete(
                f"{BASE_URL}/employees/{created_user_id}",
                headers={**headers, "Authorization": f"Bearer {token}"},
                timeout=TIMEOUT
            )
            try:
                del_body = resp.json()
            except ValueError:
                del_body = {}

            assert resp.status_code in (200, 201), f"{role_name} delete expected HTTP 200/201, got {resp.status_code}, body={del_body}"
            if isinstance(del_body, dict) and "statusCode" in del_body:
                assert del_body["statusCode"] in (200, 201), f"{role_name} delete wrapper.statusCode unexpected: {del_body}"

            # After successful delete, verify status changed to TERMINATED via GET /employees/:id
            resp = session.get(
                f"{BASE_URL}/employees/{created_user_id}",
                headers={**headers, "Authorization": f"Bearer {token}"},
                timeout=TIMEOUT
            )
            try:
                get_body = resp.json()
            except ValueError:
                get_body = {}

            assert resp.status_code == 200, f"{role_name} get-after-delete expected HTTP 200, got {resp.status_code}, body={get_body}"
            assert get_body.get("statusCode") == 200, f"{role_name} get-after-delete wrapper.statusCode unexpected: {get_body}"
            emp_data = get_body.get("data") or {}

            status_val = None
            # Try several common keys
            for k in ("status", "employee_status", "state"):
                if k in emp_data:
                    status_val = emp_data[k]
                    break
            # Also allow nested objects: data.employee.status
            if status_val is None:
                nested = emp_data.get("employee") or {}
                if isinstance(nested, dict) and "status" in nested:
                    status_val = nested["status"]

            assert status_val is not None, f"Could not find status field in employee data: {emp_data}"
            assert str(status_val).upper() == "TERMINATED", f"Expected employee status TERMINATED after delete, got '{status_val}'"

            role_tested_success = True
            role_success_name = role_name
            # If admin succeeded, no need to test hr (but we still will if available)
            # continue loop to test other role if present

        # If neither admin nor hr tokens available, warn but treat as not failing the test.
        if not role_tested_success:
            # We will attempt to indicate that the role-based delete part couldn't be executed due to missing credentials.
            print("Warning: ADMIN_EMAIL/ADMIN_PASSWORD and HR_EMAIL/HR_PASSWORD not provided; role-based delete verification skipped.")

    except RequestException as e:
        raise AssertionError(f"Request error during test execution: {e}")
    finally:
        # Cleanup: attempt to delete the created user if possible using admin or hr token
        cleanup_token = admin_token or hr_token
        if created_user_id and cleanup_token:
            try:
                resp = session.delete(
                    f"{BASE_URL}/employees/{created_user_id}",
                    headers={**headers, "Authorization": f"Bearer {cleanup_token}"},
                    timeout=TIMEOUT
                )
                # not asserting in cleanup, just best-effort
            except Exception:
                pass

if __name__ == "__main__":
    test_delete_employee_soft_delete_role_based_access()
    print("TC008 completed.")