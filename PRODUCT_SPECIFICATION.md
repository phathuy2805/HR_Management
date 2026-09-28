# Human Resource Management (HRM) System - Product Specification Document (PRD)

## 1. Overview & Architecture
- **Framework**: NestJS v12 (TypeScript)
- **Database & ORM**: PostgreSQL 15, Prisma ORM
- **Authentication**: JWT Bearer Token (`Authorization: Bearer <token>`).
- **Base URL**: `http://localhost:3000`
- **Global Response Format**:
  All successful responses return HTTP status with standard structure:
  ```json
  {
    "success": true,
    "statusCode": 200,
    "data": { ... },
    "timestamp": "ISO_DATE_STRING"
  }
  ```
- **Error Response Format**:
  ```json
  {
    "statusCode": 400,
    "message": "Error details or array of validation errors",
    "error": "Bad Request"
  }
  ```
- **Roles & Permissions**:
  - `USER`: Regular employee (can register, view profile, manage own leave requests, view own payrolls).
  - `MANAGER`: Direct line manager (can approve level 1 leave requests).
  - `HR_MANAGER`: HR Administrator (can manage employees, approve level 2 leave requests, process payrolls).
  - `ADMIN`: System Administrator (full access).

---

## 2. API Endpoints & Business Logic

### 2.1 Authentication (`/auth`)
- **`POST /auth/register`** (Public):
  - Request Body:
    ```json
    {
      "first_name": "Nguyen",
      "last_name": "Van A",
      "email": "user@company.com",
      "password": "Password123@",
      "confirm_password": "Password123@"
    }
    ```
  - Validation: Email must be valid format, password >= 6 characters, `confirm_password` must match `password`.
  - Response `201 Created`: Returns employee object with password omitted.
  - Errors: `400 Bad Request` (validation error), `409 Conflict` (email already exists).

- **`POST /auth/login`** (Public):
  - Request Body:
    ```json
    {
      "email": "user@company.com",
      "password": "Password123@"
    }
    ```
  - Response `201 Created`: Returns `{ "access_token": "...", "refresh_token": "..." }`.
  - Errors: `401 Unauthorized` (invalid credentials or status is `TERMINATED`).

---

### 2.2 Profile (`/profile`)
- **`GET /profile`** (Requires Bearer Token):
  - Returns current logged-in user profile, including department, job title, and manager relations.
  - Response `200 OK`.

---

### 2.3 Employees Management (`/employees`)
- **`POST /employees`** (Requires `HR_MANAGER` or `ADMIN`):
  - Request Body:
    ```json
    {
      "first_name": "Tran",
      "last_name": "Van B",
      "email": "employee@company.com",
      "password": "Password123@",
      "role": "USER",
      "department_id": 1,
      "job_title_id": 1,
      "manager_id": null,
      "status": "ACTIVE"
    }
    ```
  - Response `201 Created`: Returns created employee record with `id`.

- **`GET /employees`** (Requires `HR_MANAGER` or `ADMIN`):
  - Query params: `page` (default 1), `limit` (default 10), `search`, `department_id`.
  - Response `200 OK`: Returns `{ "data": [...], "total": 10, "page": 1, "limit": 10, "totalPages": 1 }`.

- **`GET /employees/:id`** (Requires `HR_MANAGER` or `ADMIN`):
  - Response `200 OK`: Returns single employee details.

- **`PATCH /employees/:id`** (Requires `HR_MANAGER` or `ADMIN`):
  - Request Body: Updatable fields (`first_name`, `last_name`, `email`, `role`, `department_id`, etc.).
  - Response `200 OK`: Returns updated employee record.

- **`DELETE /employees/:id`** (Requires `HR_MANAGER` or `ADMIN`):
  - Sets employee status to `TERMINATED`.
  - Response `200 OK`.

---

### 2.4 Leave Requests Workflow (`/leave-requests`)
- **`POST /leave-requests`** (Requires Bearer Token):
  - Request Body:
    ```json
    {
      "start_date": "2026-10-01",
      "end_date": "2026-10-03",
      "type": "VACATION",
      "reason": "Family vacation"
    }
    ```
  - Creates request with status `PENDING`.
  - Response `201 Created`: Returns leave request record with `id` and status `PENDING`.

- **`GET /leave-requests/my-requests`** (Requires Bearer Token):
  - Returns list of leave requests for the authenticated user.
  - Response `200 OK`.

- **`PATCH /leave-requests/:id/approve-manager`** (Requires `MANAGER`):
  - Updates leave request status to `APPROVED_BY_MANAGER`.
  - Response `200 OK`.

- **`PATCH /leave-requests/:id/approve-hr`** (Requires `HR_MANAGER`):
  - Updates leave request status to `APPROVED_BY_HR`.
  - Response `200 OK`.

- **`PATCH /leave-requests/:id/reject`** (Requires `MANAGER` or `HR_MANAGER`):
  - Updates leave request status to `REJECTED`.
  - Response `200 OK`.

---

### 2.5 Payroll Management (`/payrolls`)
- **`POST /payrolls/process`** (Requires `HR_MANAGER`):
  - Request Body:
    ```json
    {
      "pay_period_start": "2026-09-01",
      "pay_period_end": "2026-09-30"
    }
    ```
  - Calculates payrolls for all `ACTIVE` employees, subtracting daily deduction for unapproved leaves (standard 22 working days per month).
  - Response `201 Created`: Returns list of created payrolls.

- **`GET /payrolls/my-payrolls`** (Requires Bearer Token):
  - Returns current user's payroll records with pagination.
  - Response `200 OK`.

- **`GET /payrolls`** (Requires `HR_MANAGER` or `ADMIN`):
  - Returns all payrolls in the system with pagination.
  - Response `200 OK`.

- **`GET /payrolls/:id`** (Requires Bearer Token):
  - Returns single payroll details (USER can only view own; ADMIN/HR can view any).
  - Response `200 OK`.
