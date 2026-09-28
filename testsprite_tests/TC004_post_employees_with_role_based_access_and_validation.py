import os
import requests
import uuid
import sys
import time

BASE_URL = "http://localhost:3000"
TIMEOUT = 30


def _get_json_safe(resp):
    try:
        return resp.json()
    except Exception:
        return None


def _extract_wrapped_status(resp_json):
    if isinstance(resp_json, dict) and "statusCode" in resp_json:
        return resp_json.get("statusCode")
    return None


def login(email, password):
    url = f"{BASE_URL}/auth/login"
    payload = {"email": email, "password": password}
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    j = _get_json_safe(resp)
    if resp.status_code in (200, 201) and j and j.get("data") and j["data"].get("access_token"):
        return j["data"]["access_token"]
    raise RuntimeError(f"Login failed for {email}: status={resp.status_code}, body={j}")


def try_login_from_env(role_key):
    # role_key examples: 'ADMIN', 'HR_MANAGER', 'USER'
    token_env = os.getenv(f"{role_key}_TOKEN")
    if token_env:
        return token_env

    email = os.getenv(f"{role_key}_EMAIL")
    password = os.getenv(f"{role_key}_PASSWORD")
    if email and password:
        return login(email, password)
    return None


def create_employee(payload, token):
    url = f"{BASE_URL}/employees"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    return resp


def delete_employee(emp_id, token):
    url = f"{BASE_URL}/employees/{emp_id}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
    return resp


def register_user(email, password, first_name="Temp", last_name="User"):
    url = f"{BASE_URL}/auth/register"
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "confirm_password": password,
    }
    resp = requests.post(url, json=payload, timeout=TIMEOUT)
    return resp


def get_profile(token):
    url = f"{BASE_URL}/profile"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    return resp


def test_post_employees_role_based_access_and_validation():
    created_employee_ids = []
    created_temp_user = None  # dict with id and whether deletable
    # Acquire tokens from env or login
    admin_token = try_login_from_env("ADMIN") or try_login_from_env("ADMIN_USER")  # fallback
    hr_token = try_login_from_env("HR_MANAGER") or try_login_from_env("HR")
    user_token = try_login_from_env("USER")

    # At least one elevated token required to assert successful creation
    if not (admin_token or hr_token):
        raise RuntimeError(
            "No HR_MANAGER or ADMIN token available. Set HR_MANAGER_TOKEN or ADMIN_TOKEN or corresponding EMAIL/PASSWORD env vars."
        )

    elevated_token = hr_token or admin_token

    try:
        # 1) Successful creation with HR_MANAGER or ADMIN role
        unique_email = f"test.employee.{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "first_name": "Test",
            "last_name": "Employee",
            "email": unique_email,
            "password": "Password123!",
            "role": "USER"
        }
        resp = create_employee(payload, elevated_token)
        resp_json = _get_json_safe(resp)
        wrapped_status = _extract_wrapped_status(resp_json)
        # Assert HTTP status or wrapped status indicates creation
        assert resp.status_code in (200, 201), f"Expected 201, got HTTP {resp.status_code}, body={resp_json}"
        if wrapped_status is not None:
            assert wrapped_status in (200, 201), f"Expected wrapped status 201, got {wrapped_status}, body={resp_json}"
        # Verify data.id exists
        data = (resp_json or {}).get("data") if isinstance(resp_json, dict) else None
        emp_id = None
        if data and isinstance(data, dict):
            emp_id = data.get("id") or data.get("employee") and data["employee"].get("id")
        # Fallback: if id not in wrapper, try GET /employees with filters not available; require id to cleanup
        assert emp_id, f"Created employee id not found in response body: {resp_json}"
        created_employee_ids.append(emp_id)

        # 2) Successful creation with ADMIN role as well (if different token available)
        if admin_token and admin_token != elevated_token:
            unique_email2 = f"test.employee.{uuid.uuid4().hex[:8]}@example.com"
            payload2 = {
                "first_name": "Admin",
                "last_name": "Created",
                "email": unique_email2,
                "password": "Password123!",
                "role": "MANAGER"
            }
            resp2 = create_employee(payload2, admin_token)
            resp2_json = _get_json_safe(resp2)
            wrapped_status2 = _extract_wrapped_status(resp2_json)
            assert resp2.status_code in (200, 201), f"Admin creation expected 201, got {resp2.status_code}, body={resp2_json}"
            if wrapped_status2 is not None:
                assert wrapped_status2 in (200, 201), f"Admin creation wrapped status expected 201, got {wrapped_status2}, body={resp2_json}"
            data2 = (resp2_json or {}).get("data") if isinstance(resp2_json, dict) else None
            emp_id2 = None
            if data2 and isinstance(data2, dict):
                emp_id2 = data2.get("id") or data2.get("employee") and data2["employee"].get("id")
            assert emp_id2, f"Admin-created employee id not found: {resp2_json}"
            created_employee_ids.append(emp_id2)

        # 3) Verify 403 Forbidden for insufficient roles (USER)
        # Acquire a non-privileged user token. Prefer env-provided, else attempt register+login.
        temp_user_registered = False
        if not user_token:
            # Attempt to register a temporary user (will produce a user account)
            temp_email = f"temp.user.{uuid.uuid4().hex[:8]}@example.com"
            temp_password = "TempPass123!"
            reg_resp = register_user(temp_email, temp_password, first_name="Temp", last_name="User")
            reg_json = _get_json_safe(reg_resp)
            # Registration might return 201 and data with created user id
            if reg_resp.status_code in (200, 201):
                try:
                    user_token = login(temp_email, temp_password)
                    temp_user_registered = True
                    # attempt to get profile id (the created user id). Need admin token to delete later; we'll record profile info
                    profile_resp = get_profile(user_token)
                    profile_json = _get_json_safe(profile_resp)
                    profile_data = (profile_json or {}).get("data") if isinstance(profile_json, dict) else None
                    created_temp_user = {"email": temp_email, "id": profile_data.get("id") if profile_data else None, "password": temp_password}
                except Exception:
                    # continue; we may still have user_token or not
                    user_token = None
            else:
                # registration failed; do not create temp user
                user_token = None

        if user_token:
            # Use user token to attempt to create employee -> expect 403 Forbidden
            unique_email3 = f"test.employee.{uuid.uuid4().hex[:8]}@example.com"
            payload3 = {
                "first_name": "Insufficient",
                "last_name": "Role",
                "email": unique_email3,
                "password": "Password123!",
                "role": "USER"
            }
            resp3 = create_employee(payload3, user_token)
            resp3_json = _get_json_safe(resp3)
            wrapped_status3 = _extract_wrapped_status(resp3_json)
            # Accept either HTTP 403 or wrapped statusCode 403. Sometimes server may respond 401 if token lacks privileges or is invalid.
            assert resp3.status_code in (401, 403), f"Expected 403/401 for insufficient role, got {resp3.status_code}, body={resp3_json}"
            if wrapped_status3 is not None:
                assert wrapped_status3 in (401, 403), f"Expected wrapped 403/401, got {wrapped_status3}, body={resp3_json}"
        else:
            # No user token available; assert that attempting without token yields 401 Unauthorized when creating employee
            unique_email3 = f"test.employee.{uuid.uuid4().hex[:8]}@example.com"
            payload3 = {
                "first_name": "Insufficient",
                "last_name": "Role",
                "email": unique_email3,
                "password": "Password123!",
                "role": "USER"
            }
            resp3 = create_employee(payload3, None)
            resp3_json = _get_json_safe(resp3)
            wrapped_status3 = _extract_wrapped_status(resp3_json)
            assert resp3.status_code in (401, 403), f"Expected 401/403 when token missing, got {resp3.status_code}, body={resp3_json}"
            if wrapped_status3 is not None:
                assert wrapped_status3 in (401, 403), f"Expected wrapped 401/403, got {wrapped_status3}, body={resp3_json}"

        # 4) POST /employees with missing or malformed data -> Bad Request 400
        bad_payload = {
            # missing required fields like first_name and email; malformed password maybe
            "last_name": "NoFirst",
            "email": "not-an-email",
            "password": "123"
        }
        resp4 = create_employee(bad_payload, elevated_token)
        resp4_json = _get_json_safe(resp4)
        wrapped_status4 = _extract_wrapped_status(resp4_json)
        # Expect HTTP 400 or wrapped 400
        assert resp4.status_code == 400 or (wrapped_status4 == 400), f"Expected 400 for malformed data, got HTTP {resp4.status_code}, wrapped={wrapped_status4}, body={resp4_json}"

        print("TC004 passed: role-based create and validation checks succeeded.")

    finally:
        # Cleanup created employees using admin_token preferred then hr_token
        cleanup_token = admin_token or hr_token
        for emp_id in created_employee_ids:
            try:
                resp_del = delete_employee(emp_id, cleanup_token)
                j = _get_json_safe(resp_del)
                if resp_del.status_code not in (200, 204):
                    print(f"Warning: deleting employee {emp_id} returned status {resp_del.status_code}, body={j}")
            except Exception as e:
                print(f"Error deleting employee {emp_id}: {e}")

        # If we registered a temporary user and have admin token, remove that user as employee
        if created_temp_user and created_temp_user.get("id") and admin_token:
            try:
                resp_del2 = delete_employee(created_temp_user["id"], admin_token)
                j2 = _get_json_safe(resp_del2)
                if resp_del2.status_code not in (200, 204):
                    print(f"Warning: deleting temp user {created_temp_user['id']} returned {resp_del2.status_code}, body={j2}")
            except Exception as e:
                print(f"Error deleting temp user {created_temp_user.get('id')}: {e}")


if __name__ == "__main__":
    try:
        test_post_employees_role_based_access_and_validation()
    except AssertionError as ae:
        print(f"AssertionError: {ae}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)
    else:
        print("Test completed successfully.")
        sys.exit(0)