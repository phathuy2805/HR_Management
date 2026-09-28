import os
import time
import uuid
import requests

BASE_URL = "http://localhost:3000"
TIMEOUT = 30


def get_admin_token():
    """
    Try to obtain an admin/HR_MANAGER token from environment or by logging in.
    Environment variables checked:
      - ADMIN_TOKEN (direct JWT)
      - ADMIN_EMAIL and ADMIN_PASSWORD (to perform /auth/login)
    Raises AssertionError if no credentials are available or authentication fails.
    """
    admin_token = os.environ.get("ADMIN_TOKEN")
    if admin_token:
        return admin_token

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if admin_email and admin_password:
        url = f"{BASE_URL}/auth/login"
        payload = {"email": admin_email, "password": admin_password}
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        try:
            resp_json = resp.json()
        except ValueError:
            raise AssertionError(f"Admin login failed, non-JSON response: {resp.status_code} {resp.text}")
        assert resp.status_code == 201 and resp_json.get("success") is True, f"Admin login failed: {resp_json}"
        data = resp_json.get("data") or {}
        token = data.get("access_token")
        assert token, "Admin login did not return access_token"
        return token

    raise AssertionError("Admin credentials not provided. Set ADMIN_TOKEN or ADMIN_EMAIL and ADMIN_PASSWORD env vars.")


def register_user(first_name, last_name, email, password):
    url = f"{BASE_URL}/auth/register"
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "confirm_password": password,
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    try:
        j = resp.json()
    except ValueError:
        raise AssertionError(f"Register returned non-JSON response: {resp.status_code} {resp.text}")
    assert resp.status_code == 201 and j.get("success") is True and j.get("statusCode") == 201, f"Unexpected register response: {j}"
    data = j.get("data") or {}
    # data should include created employee id; try multiple keys
    emp_id = data.get("id") or data.get("employee", {}).get("id") or data.get("user", {}).get("id")
    # if not found, maybe entire data is the employee with id under different key; fallback to search
    if not emp_id:
        # if data has numeric keys or 'email' matching, attempt to use provided email to find id maybe not possible; fail gracefully
        raise AssertionError(f"Register did not return employee id in data: {data}")
    return emp_id


def login(email, password):
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    try:
        j = resp.json()
    except ValueError:
        raise AssertionError(f"Login returned non-JSON response: {resp.status_code} {resp.text}")
    assert resp.status_code == 201 and j.get("success") is True and j.get("statusCode") == 201, f"Login failed: {j}"
    token = (j.get("data") or {}).get("access_token")
    assert token, f"Login did not return access_token: {j}"
    return token


def delete_employee(emp_id, admin_token):
    url = f"{BASE_URL}/employees/{emp_id}"
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
    # Attempt cleanup; accept 200 or 204 depending on implementation, but expect TransformInterceptor wrapper if JSON
    if resp.status_code in (200, 204):
        try:
            j = resp.json()
            # If wrapper present, ensure statusCode 200
            if isinstance(j, dict) and "statusCode" in j:
                assert j.get("statusCode") == 200, f"Unexpected delete response wrapper: {j}"
        except ValueError:
            # non-json 204 or other responses are acceptable for cleanup
            pass
    else:
        # Non-successful cleanup should be noted but not raise to avoid masking original errors in finally
        print(f"Warning: failed to delete employee {emp_id}. Status: {resp.status_code}, Body: {resp.text}")


def test_patch_employees_update_with_valid_data_and_roles():
    # Prepare unique user data
    unique_suffix = str(int(time.time())) + "_" + uuid.uuid4().hex[:8]
    user_email = f"user_{unique_suffix}@example.com"
    user_password = "Password123!"
    first_name = "Test"
    last_name = "User"

    admin_token = get_admin_token()

    created_emp_id = None
    # Create a user via public registration to serve as the target employee to update
    try:
        created_emp_id = register_user(first_name, last_name, user_email, user_password)
        assert created_emp_id, "Failed to obtain created employee ID from registration."

        # Login as the newly registered (normal) user to get a non-privileged token
        user_token = login(user_email, user_password)

        # Attempt to PATCH the employee as a non-privileged user -> should be forbidden (403)
        url = f"{BASE_URL}/employees/{created_emp_id}"
        headers_user = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        patch_payload = {"first_name": "UnauthorizedUpdateAttempt"}
        resp_user_patch = requests.patch(url, json=patch_payload, headers=headers_user, timeout=TIMEOUT)
        # Expect 403 Forbidden. The TransformInterceptor wraps responses; check wrapper or HTTP status.
        try:
            j = resp_user_patch.json()
            # If wrapper present, check statusCode == 403
            if isinstance(j, dict) and "statusCode" in j:
                assert j.get("statusCode") == 403, f"Expected 403 for user patch, got wrapper: {j}"
            else:
                assert resp_user_patch.status_code == 403, f"Expected 403 for user patch, got {resp_user_patch.status_code}"
        except ValueError:
            # Non-JSON response; assert HTTP status
            assert resp_user_patch.status_code == 403, f"Expected 403 for user patch, got {resp_user_patch.status_code}"

        # Now perform the PATCH as admin/HR (privileged) -> should succeed with statusCode 200 and updated data returned
        headers_admin = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        updated_first_name = "UpdatedName"
        patch_payload_admin = {"first_name": updated_first_name, "last_name": "UpdatedLast"}
        resp_admin_patch = requests.patch(url, json=patch_payload_admin, headers=headers_admin, timeout=TIMEOUT)
        try:
            j2 = resp_admin_patch.json()
        except ValueError:
            raise AssertionError(f"Admin patch returned non-JSON response: {resp_admin_patch.status_code} {resp_admin_patch.text}")

        assert resp_admin_patch.status_code == 200, f"Admin patch expected HTTP 200, got {resp_admin_patch.status_code} with body {j2}"
        assert j2.get("success") is True, f"Admin patch returned success != True: {j2}"
        assert j2.get("statusCode") == 200, f"Admin patch wrapper statusCode is not 200: {j2}"
        data = j2.get("data") or {}
        # Validate the updated fields are reflected in the response data
        returned_first = data.get("first_name") or data.get("firstName") or data.get("first")
        returned_last = data.get("last_name") or data.get("lastName") or data.get("last")
        assert returned_first == updated_first_name, f"Expected updated first_name '{updated_first_name}', got '{returned_first}'"
        assert returned_last == "UpdatedLast", f"Expected updated last_name 'UpdatedLast', got '{returned_last}'"

        # Optionally, verify role-based update: attempt to set role via admin token (valid enum HR_MANAGER or ADMIN)
        new_role = "HR_MANAGER"
        patch_payload_role = {"role": new_role}
        resp_admin_role_patch = requests.patch(url, json=patch_payload_role, headers=headers_admin, timeout=TIMEOUT)
        try:
            j3 = resp_admin_role_patch.json()
        except ValueError:
            raise AssertionError(f"Admin role patch returned non-JSON response: {resp_admin_role_patch.status_code} {resp_admin_role_patch.text}")

        assert resp_admin_role_patch.status_code == 200 and j3.get("success") is True and j3.get("statusCode") == 200, f"Admin role patch failed: {j3}"
        data_role = j3.get("data") or {}
        returned_role = data_role.get("role")
        # Role may or may not be returned; if returned, ensure it matches requested role
        if returned_role is not None:
            assert returned_role == new_role, f"Expected role '{new_role}', got '{returned_role}'"

    finally:
        # Cleanup: delete created employee using admin token if we have an id
        if created_emp_id:
            try:
                delete_employee(created_emp_id, admin_token)
            except Exception as e:
                print(f"Cleanup delete failed for employee {created_emp_id}: {e}")


if __name__ == "__main__":
    test_patch_employees_update_with_valid_data_and_roles()