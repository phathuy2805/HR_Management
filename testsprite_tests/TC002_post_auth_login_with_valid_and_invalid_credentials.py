import requests
import uuid
import time

BASE_URL = "http://localhost:3000"
TIMEOUT = 30.0
HEADERS = {"Content-Type": "application/json"}


def _parse_transform_wrapper(resp):
    """
    Parse response expecting TransformInterceptor wrapper:
    { success, statusCode, data, timestamp }
    Returns a tuple (wrapper_dict, raw_json)
    If parsing fails, wrapper_dict may be None.
    """
    try:
        j = resp.json()
    except ValueError:
        return None, None
    if isinstance(j, dict) and all(k in j for k in ("success", "statusCode", "data", "timestamp")):
        return j, j.get("data")
    return None, j


def test_auth_login_valid_invalid_terminated():
    # Prepare unique test user
    unique = uuid.uuid4().hex[:8]
    email = f"testuser_{unique}@example.com"
    password = "Password123@"
    register_payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": password,
        "confirm_password": password,
    }

    created_user_id = None

    try:
        # 1) Create a new user via /auth/register
        try:
            resp = requests.post(
                f"{BASE_URL}/auth/register",
                json=register_payload,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise AssertionError(f"Request to register failed: {e}")

        wrapper, data = _parse_transform_wrapper(resp)
        # Expect 201 either as HTTP status or wrapper.statusCode
        if resp.status_code != 201 and not (wrapper and wrapper.get("statusCode") == 201):
            raise AssertionError(
                f"Expected register to return 201, got HTTP {resp.status_code}, wrapper: {wrapper}"
            )
        # Extract created user id if available
        if isinstance(data, dict):
            # Common possible shapes: data contains 'id' or 'employee' or entire user object
            created_user_id = data.get("id") or data.get("user_id") or data.get("employee", {}).get("id")
            # fallback: if data has 'email' and matches our email, maybe id key is 'id'
            if not created_user_id and data.get("email") == email and "id" in data:
                created_user_id = data["id"]

        # 2) Successful login with valid credentials
        login_payload = {"email": email, "password": password}
        try:
            resp_login = requests.post(
                f"{BASE_URL}/auth/login",
                json=login_payload,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise AssertionError(f"Request to login (valid credentials) failed: {e}")

        wrapper_login, data_login = _parse_transform_wrapper(resp_login)
        if resp_login.status_code != 201 and not (wrapper_login and wrapper_login.get("statusCode") == 201):
            raise AssertionError(
                f"Expected login success (201) for valid credentials, got HTTP {resp_login.status_code}, wrapper: {wrapper_login}"
            )
        # Verify tokens exist in wrapper data
        if not isinstance(data_login, dict):
            raise AssertionError(f"Login response data missing or not an object: {data_login}")
        access_token = data_login.get("access_token")
        refresh_token = data_login.get("refresh_token")
        assert isinstance(access_token, str) and access_token.strip() != "", "access_token missing or empty"
        assert isinstance(refresh_token, str) and refresh_token.strip() != "", "refresh_token missing or empty"

        # 3) Unauthorized error with invalid credentials
        bad_login_payload = {"email": email, "password": "WrongPassword!"}
        try:
            resp_bad = requests.post(
                f"{BASE_URL}/auth/login",
                json=bad_login_payload,
                headers=HEADERS,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise AssertionError(f"Request to login (invalid credentials) failed: {e}")

        wrapper_bad, data_bad = _parse_transform_wrapper(resp_bad)
        # Expect 401 either as HTTP status or wrapper.statusCode
        if resp_bad.status_code != 401 and not (wrapper_bad and wrapper_bad.get("statusCode") == 401):
            raise AssertionError(
                f"Expected 401 for invalid credentials, got HTTP {resp_bad.status_code}, wrapper: {wrapper_bad}"
            )

        # 4) Terminated user login -> Attempt to terminate the created user, then verify login returns 401
        if not created_user_id:
            # If we don't have an id, try to infer from register data shape
            # Attempt to fetch by logging in and hitting /profile to see id if available
            created_user_id = None  # remain None

        if not created_user_id:
            # Try a naive approach: some register responses return entire user object as data with field 'email' but no id.
            # If no id, we cannot attempt termination via /employees/:id and therefore cannot validate terminated-account behavior.
            raise AssertionError("Could not determine created user id from register response; cannot test terminated account flow")

        # Attempt to delete the employee to set status to TERMINATED
        try:
            resp_delete = requests.delete(
                f"{BASE_URL}/employees/{created_user_id}",
                headers=HEADERS,
                timeout=TIMEOUT,
            )
        except requests.RequestException as e:
            raise AssertionError(f"Request to delete employee (to terminate) failed: {e}")

        wrapper_delete, data_delete = _parse_transform_wrapper(resp_delete)

        # If deletion succeeded (200), then login should be unauthorized (401)
        if resp_delete.status_code == 200 or (wrapper_delete and wrapper_delete.get("statusCode") == 200):
            # Wait a moment to let backend apply termination state
            time.sleep(0.5)
            try:
                resp_login_terminated = requests.post(
                    f"{BASE_URL}/auth/login",
                    json=login_payload,
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )
            except requests.RequestException as e:
                raise AssertionError(f"Request to login (terminated user) failed: {e}")

            wrapper_term, data_term = _parse_transform_wrapper(resp_login_terminated)
            if resp_login_terminated.status_code != 401 and not (wrapper_term and wrapper_term.get("statusCode") == 401):
                raise AssertionError(
                    f"Expected 401 for terminated user login, got HTTP {resp_login_terminated.status_code}, wrapper: {wrapper_term}"
                )
        else:
            # Deletion did not succeed — likely requires elevated privileges.
            # Fail the test, indicating inability to verify terminated-user behavior in this environment.
            raise AssertionError(
                f"Could not terminate user {created_user_id}. DELETE returned HTTP {resp_delete.status_code}, wrapper: {wrapper_delete}"
            )

    finally:
        # Cleanup: attempt to delete created user if id known.
        if created_user_id:
            try:
                requests.delete(
                    f"{BASE_URL}/employees/{created_user_id}",
                    headers=HEADERS,
                    timeout=TIMEOUT,
                )
            except requests.RequestException:
                # Best-effort cleanup; ignore errors here.
                pass


if __name__ == "__main__":
    test_auth_login_valid_invalid_terminated()
    print("TC002 executed.")