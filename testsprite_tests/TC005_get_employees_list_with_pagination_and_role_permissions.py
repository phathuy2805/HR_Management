import os
import uuid
import requests
import sys

BASE_URL = "http://localhost:3000"
TIMEOUT = 30


def test_get_employees_pagination_and_permissions():
    # Helper functions
    def register_user(email, password, first_name="Test", last_name="User"):
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
            body = resp.json()
        except ValueError:
            raise AssertionError(f"Register response is not JSON: HTTP {resp.status_code} - {resp.text}")
        return resp, body

    def login_user(email, password):
        url = f"{BASE_URL}/auth/login"
        payload = {"email": email, "password": password}
        resp = requests.post(url, json=payload, timeout=TIMEOUT)
        try:
            body = resp.json()
        except ValueError:
            raise AssertionError(f"Login response is not JSON: HTTP {resp.status_code} - {resp.text}")
        return resp, body

    def get_employees(token):
        url = f"{BASE_URL}/employees"
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = requests.get(url, headers=headers, params={"page": 1, "limit": 10}, timeout=TIMEOUT)
        try:
            body = resp.json()
        except ValueError:
            raise AssertionError(f"GET /employees response is not JSON: HTTP {resp.status_code} - {resp.text}")
        return resp, body

    def delete_employee(employee_id, admin_token):
        url = f"{BASE_URL}/employees/{employee_id}"
        headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}
        resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
        try:
            body = resp.json()
        except ValueError:
            body = None
        return resp, body

    # Create a unique regular user and test permissions
    unique_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "Password123!"

    created_user_id = None
    admin_token = os.getenv("ADMIN_TOKEN") or os.getenv("HR_MANAGER_TOKEN")  # allow either token for cleanup and privileged checks

    try:
        # Register regular user
        resp_reg, body_reg = register_user(unique_email, password)
        assert resp_reg.status_code in (200, 201), f"Expected 201 on register, got {resp_reg.status_code}: {body_reg}"
        # Expect TransformInterceptor wrapper
        assert isinstance(body_reg, dict), "Register response body must be a JSON object"
        assert "statusCode" in body_reg, f"Register wrapper missing statusCode: {body_reg}"
        assert body_reg["statusCode"] in (200, 201), f"Unexpected register wrapper statusCode: {body_reg}"
        created_user_id = None
        if isinstance(body_reg.get("data"), dict):
            created_user_id = body_reg["data"].get("id") or body_reg["data"].get("employee_id")

        # Login as the newly registered regular user
        resp_login, body_login = login_user(unique_email, password)
        assert resp_login.status_code in (200, 201), f"Expected 201 on login, got {resp_login.status_code}: {body_login}"
        assert isinstance(body_login, dict) and "data" in body_login and isinstance(body_login["data"], dict), "Login wrapper missing data"
        access_token = body_login["data"].get("access_token")
        assert access_token, f"No access_token returned on login: {body_login}"

        # Attempt to GET /employees as a regular user -> expect 403 Forbidden
        resp_get, body_get = get_employees(access_token)
        # Accept either HTTP 403 or wrapper statusCode == 403 to validate forbidden
        if resp_get.status_code != 403:
            # Check wrapper
            assert isinstance(body_get, dict), f"Unexpected GET /employees body: {body_get}"
            assert body_get.get("statusCode") == 403, f"Expected wrapper statusCode 403 for insufficient permissions, got {body_get.get('statusCode')}"
            assert body_get.get("success") is False or body_get.get("statusCode") == 403
        else:
            # HTTP 403
            assert resp_get.status_code == 403

        # If an admin/hr token is provided via environment, verify privileged access returns 200 and paginated data
        if admin_token:
            resp_admin_get, body_admin_get = get_employees(admin_token)
            assert resp_admin_get.status_code in (200, 201, 204, 400)  # allow flexibility, but we'll assert wrapper statusCode == 200
            assert isinstance(body_admin_get, dict), f"Admin GET /employees body not JSON object: {body_admin_get}"
            # wrapper should indicate success and statusCode 200 for listing
            assert body_admin_get.get("statusCode") == 200, f"Expected wrapper statusCode 200 for admin GET /employees, got {body_admin_get.get('statusCode')}"
            assert body_admin_get.get("success") is True
            data = body_admin_get.get("data")
            assert data is not None, "Expected data in admin GET /employees response"
            # data should be either a list of employees or an object containing items/list and pagination metadata
            if isinstance(data, list):
                # OK: list of employees
                pass
            elif isinstance(data, dict):
                # Common paginated shapes: items, results, data, meta
                possible_lists = []
                for k in ("items", "results", "data", "employees"):
                    if isinstance(data.get(k), list):
                        possible_lists.append(k)
                # Accept if at least one list-like field is present
                assert possible_lists or any(isinstance(v, list) for v in data.values()), f"Paginated data missing list inside object: {data}"
        else:
            # If no admin token available, we just validate that regular user was forbidden (done above)
            pass

    except requests.RequestException as e:
        raise AssertionError(f"Network error during test: {e}")
    finally:
        # Attempt cleanup: delete created user if we have created_user_id and admin token
        if created_user_id and admin_token:
            try:
                resp_del, body_del = delete_employee(created_user_id, admin_token)
                # Accept 200 or 204 as success. If wrapper exists, check wrapper statusCode.
                if resp_del.status_code not in (200, 204):
                    # If wrapper present, check its statusCode
                    if isinstance(body_del, dict) and "statusCode" in body_del:
                        assert body_del["statusCode"] in (200, 204), f"Failed to delete created user via admin token: {body_del}"
                    else:
                        # Not successful deletion
                        raise AssertionError(f"Failed to delete created user, HTTP {resp_del.status_code}: {resp_del.text}")
            except requests.RequestException as e:
                # Cleanup failure should not mask test result but we assert to surface the issue
                raise AssertionError(f"Network error during cleanup delete: {e}")


if __name__ == "__main__":
    try:
        test_get_employees_pagination_and_permissions()
        print("TC005 passed")
    except AssertionError as e:
        print(f"TC005 failed: {e}")
        sys.exit(1)
    except Exception as ex:
        print(f"TC005 error: {ex}")
        sys.exit(2)