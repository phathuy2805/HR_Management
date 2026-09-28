import os
import time
import uuid
import requests

BASE_URL = "http://localhost:3000"
TIMEOUT = 30


def _post(path, token=None, json=None, timeout=TIMEOUT):
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(url, json=json, headers=headers, timeout=timeout)


def _delete(path, token=None, timeout=TIMEOUT):
    url = BASE_URL + path
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.delete(url, headers=headers, timeout=timeout)


def _parse_wrapped_response(resp):
    try:
        body = resp.json()
    except ValueError:
        raise AssertionError(f"Response is not JSON. Status: {resp.status_code}, Text: {resp.text}")
    # Expect wrapper: { success, statusCode, data, timestamp }
    if not all(k in body for k in ("success", "statusCode", "data", "timestamp")):
        raise AssertionError(f"Response JSON missing expected wrapper keys: {body}")
    return body


def register_user(email, password, first_name="Test", last_name="User"):
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "confirm_password": password,
    }
    resp = _post("/auth/register", json=payload)
    body = _parse_wrapped_response(resp)
    assert body["statusCode"] in (201, ), f"Expected 201 on register, got {body['statusCode']}: {body}"
    return body["data"]  # expected to contain created user, including id and email


def login_user(email, password):
    payload = {"email": email, "password": password}
    resp = _post("/auth/login", json=payload)
    body = _parse_wrapped_response(resp)
    assert body["statusCode"] in (201,), f"Expected 201 on login, got {body['statusCode']}: {body}"
    data = body["data"]
    access_token = data.get("access_token")
    assert access_token, f"No access_token in login response: {data}"
    return access_token


def create_employee_as_admin(admin_token, first_name, last_name, email, password, role):
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": password,
        "role": role,
    }
    resp = _post("/employees", token=admin_token, json=payload)
    body = _parse_wrapped_response(resp)
    # Should be 201 on success
    assert body["statusCode"] in (201,), f"Expected 201 creating employee, got {body['statusCode']}: {body}"
    return body["data"]


def delete_employee(employee_id, admin_token):
    resp = _delete(f"/employees/{employee_id}", token=admin_token)
    # Some APIs may wrap delete response too
    try:
        body = _parse_wrapped_response(resp)
        # Delete success likely returns 200
        assert body["statusCode"] in (200, ), f"Unexpected statusCode on delete: {body}"
    except AssertionError:
        # If wrapper missing or something else, fallback to HTTP status
        assert resp.status_code in (200, 204), f"Failed to delete employee id {employee_id}. Status: {resp.status_code}, Text: {resp.text}"


def test_post_payrolls_process_role_and_validation():
    # Unique test users
    suffix = str(int(time.time())) + "-" + uuid.uuid4().hex[:6]
    non_hr_email = f"nonhr-{suffix}@example.com"
    non_hr_password = "Password123@"
    created_non_hr = None
    created_hr = None
    created_hr_id = None
    admin_token = None
    hr_token = None

    # Check for admin credentials in env to enable creation/deletion of employees
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    # Also allow direct HR credentials from env if provided
    HR_EMAIL = os.environ.get("HR_EMAIL")
    HR_PASSWORD = os.environ.get("HR_PASSWORD")

    try:
        # 1) Register and login a non-HR user
        created_non_hr = register_user(non_hr_email, non_hr_password, first_name="NonHR", last_name="Tester")
        non_hr_token = login_user(non_hr_email, non_hr_password)

        # 2) Unauthorized role test: non-HR user should get 403 when calling /payrolls/process
        valid_payload = {
            "pay_period_start": "2026-08-01",
            "pay_period_end": "2026-08-31"
        }
        resp = _post("/payrolls/process", token=non_hr_token, json=valid_payload)
        # Try to parse wrapper; if wrapper exists, assert statusCode==403; else assert HTTP 403
        try:
            body = _parse_wrapped_response(resp)
            assert body["statusCode"] == 403, f"Expected 403 for non-HR user, got {body['statusCode']}: {body}"
        except AssertionError:
            # If parsing wrapper failed or wrapper not present, fall back to HTTP status code check
            assert resp.status_code == 403, f"Expected HTTP 403 for non-HR user, got {resp.status_code}, body: {resp.text}"

        # 3) Prepare HR token for further tests (try env HR creds first)
        if HR_EMAIL and HR_PASSWORD:
            try:
                hr_token = login_user(HR_EMAIL, HR_PASSWORD)
            except AssertionError as e:
                hr_token = None

        # 4) If HR token not available, try to create one using ADMIN creds (if provided)
        if not hr_token and ADMIN_EMAIL and ADMIN_PASSWORD:
            admin_token = login_user(ADMIN_EMAIL, ADMIN_PASSWORD)
            # create HR employee
            hr_email = f"hr-{suffix}@example.com"
            hr_password = "Password123@"
            created_hr = create_employee_as_admin(admin_token, "HR", "Tester", hr_email, hr_password, "HR_MANAGER")
            created_hr_id = created_hr.get("id")
            # Login as created HR to obtain token
            hr_token = login_user(hr_email, hr_password)

        # If we still don't have an HR token, we cannot perform the HR-specific success and validation tests.
        if not hr_token:
            # We still validated unauthorized role above. Mark remaining as skipped by failing with clear message.
            raise AssertionError(
                "HR token not available. Provide ADMIN_EMAIL & ADMIN_PASSWORD to create HR user, "
                "or HR_EMAIL & HR_PASSWORD for an existing HR account to run full tests."
            )

        # 5) Validation test: missing pay_period_end should return 400 Bad Request when called by HR_MANAGER
        invalid_payload_missing_end = {
            "pay_period_start": "2026-08-01"
            # missing pay_period_end
        }
        resp = _post("/payrolls/process", token=hr_token, json=invalid_payload_missing_end)
        try:
            body = _parse_wrapped_response(resp)
            assert body["statusCode"] == 400, f"Expected 400 for missing pay_period_end, got {body['statusCode']}: {body}"
        except AssertionError:
            assert resp.status_code == 400, f"Expected HTTP 400 for missing pay_period_end, got {resp.status_code}, body: {resp.text}"

        # 6) Success case: HR_MANAGER with valid pay period should get 201 and a list of payrolls
        resp = _post("/payrolls/process", token=hr_token, json=valid_payload)
        body = _parse_wrapped_response(resp)
        assert body["statusCode"] == 201, f"Expected 201 for successful payroll processing, got {body['statusCode']}: {body}"
        data = body["data"]
        # Expect data to be a list (list of created payrolls)
        assert isinstance(data, list), f"Expected data to be a list of payrolls, got: {type(data)} - {data}"

    finally:
        # Cleanup created HR employee if we created one and we have admin_token
        if created_hr_id and admin_token:
            try:
                delete_employee(created_hr_id, admin_token)
            except Exception as e:
                # If delete fails, raise to make sure test run surfaces cleanup problems
                raise

        # Attempt to delete the registered non-HR user if admin credentials available and id present
        if created_non_hr and admin_token:
            created_non_hr_id = created_non_hr.get("id")
            if created_non_hr_id:
                try:
                    delete_employee(created_non_hr_id, admin_token)
                except Exception as e:
                    raise


if __name__ == "__main__":
    test_post_payrolls_process_role_and_validation()