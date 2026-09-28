# 🏢 HUMAN RESOURCE MANAGEMENT (HRM) WEB APPLICATION
> **DEFENSE CASE STUDY 5: BACKEND ENTERPRISE WITH NESTJS & POSTGRESQL**  
> *Đồ án tốt nghiệp / Bài tập lớn chuyên đề Lập trình Backend Nâng cao*

---

## 📌 1. Giới thiệu dự án
Hệ thống Quản trị Nhân sự (HRM) mô phỏng môi trường doanh nghiệp thực tế, đáp ứng các tiêu chuẩn khắt khe về:
* **Tính toàn vẹn dữ liệu:** Chuẩn hóa 3NF, ràng buộc toàn vẹn `CHECK`, cột tính toán ảo `GENERATED ALWAYS AS`, và cơ chế kiểm toán tự động bằng **Trigger PL/pgSQL** ở tầng PostgreSQL.
* **Bảo mật đa tầng (Defense-in-Depth):** Helmet, CORS, Global `ValidationPipe`, Stateless JWT, RBAC (`USER`, `MANAGER`, `HR_MANAGER`, `ADMIN`).
* **Quy trình duyệt phép 2 cấp (Dual-Approval Workflow):** Manager trực tiếp duyệt cấp 1 ➔ HR Manager duyệt cấp 2.
* **Tính lương tự động (Automated Payroll):** Khấu trừ ngày nghỉ không hợp lệ, tự động tính tổng lương.
* **Kiểm thử tự động:** Unit Test đạt độ bao phủ code (Coverage) > 89% và E2E Test toàn diện với Supertest.
* **Tài liệu hóa API:** Swagger UI chuẩn OpenAPI 3.0 tại `/api/docs`.

---

## 🛠️ 2. Tech Stack sử dụng
* **Framework:** NestJS v12+ (TypeScript)
* **Cơ sở dữ liệu:** PostgreSQL v15+
* **ORM:** Prisma ORM v6+
* **Bảo mật & Xác thực:** Passport.js, JWT (`@nestjs/jwt`), Bcrypt, Helmet, CORS
* **Validation:** `class-validator`, `class-transformer`
* **API Documentation:** Swagger UI (`@nestjs/swagger`)
* **Kiểm thử:** Vitest / Jest (Unit Test), Supertest (E2E Test)
* **Triển khai:** Docker, Docker Compose

---

## 🚀 3. Hướng dẫn cài đặt & Khởi chạy

### Cách 1: Chạy trực tiếp trên máy cục bộ (Local Development)

#### 1. Cài đặt thư viện:
```bash
npm install
```

#### 2. Cấu hình biến môi trường:
Tạo file `.env` từ file mẫu `.env.example`:
```bash
cp .env.example .env
```
Cấu hình chuỗi kết nối PostgreSQL của bạn trong `.env`:
```env
DATABASE_URL="postgresql://postgres:password@localhost:5432/hr_management?schema=public"
JWT_SECRET=super_secret_jwt_key_hr_management_2026
JWT_ACCESS_TOKEN_EXPIRE=1h
JWT_REFRESH_TOKEN_EXPIRE=7d
CORS_ORIGIN=http://localhost:3000
PORT=3000
```

#### 3. Chạy Migration và Trigger Database:
```bash
npx prisma migrate dev
```

#### 4. Khởi động ứng dụng:
```bash
# Chế độ phát triển (Watch mode)
npm run start:dev

# Chế độ Production build
npm run build
npm run start:prod
```

---

### Cách 2: Chạy toàn bộ hệ thống bằng Docker Compose (Khuyên dùng)
Chỉ với 1 câu lệnh duy nhất, Docker sẽ tự động dựng cả PostgreSQL 15 và ứng dụng NestJS:
```bash
docker compose up -d --build
```
* **API Server:** `http://localhost:3000`
* **Swagger Documentation:** `http://localhost:3000/api/docs`
* **PostgreSQL Port:** `localhost:5432`

---

## 🧪 4. Hướng dẫn chạy Kiểm thử tự động (Testing)

### 1. Kiểm thử Đơn vị (Unit Test cô lập với Mocking):
Tập trung kiểm thử logic phức tạp của `PayrollService` và `LeaveRequestsService`:
```bash
npm test
```

### 2. Xem Báo cáo Tỷ lệ Bao phủ (Coverage Report $\ge 70\%$):
```bash
npm run test:cov
```
> **Kết quả thực tế:**
> * `LeaveRequestsService`: **89.65%** Coverage
> * `PayrollsService`: **94.59%** Coverage
> *(Vượt xa chỉ tiêu $\ge 70\%$ theo yêu cầu của đề bài)*

### 3. Kiểm thử Tích hợp (E2E Test với Supertest):
Chạy toàn bộ chu kỳ yêu cầu: Đăng ký ➔ Đăng nhập nhận JWT ➔ Truy cập Profile ➔ Duyệt phép 2 cấp:
```bash
npm run test:e2e
```
*(Toàn bộ 3 kịch bản E2E Test đều PASS 100%)*

---

## 📖 5. Tài liệu API (Swagger UI)
Sau khi bật server, truy cập vào đường dẫn:
👉 **`http://localhost:3000/api/docs`**

* **Tính năng:**
  * Toàn bộ DTOs đều có mô tả tiếng Việt (`description`) và dữ liệu mẫu (`example`).
  * Tích hợp nút **Authorize (ổ khóa xanh)**: Sau khi đăng nhập tại `POST /auth/login`, copy chuỗi `access_token` dán vào để gọi thử các API được bảo vệ.
  * Phân nhóm theo các Tags: `Auth`, `Employees`, `Profile`, `Leave Requests`, `Payrolls`.

---

## 🔒 6. Bảng phân quyền Role-Based Access Control (RBAC)

| Phân hệ API | USER | MANAGER | HR_MANAGER | ADMIN |
| :--- | :---: | :---: | :---: | :---: |
| **Auth (Register / Login)** | Công khai | Công khai | Công khai | Công khai |
| **Xem Profile cá nhân (`GET /profile`)** | ✅ | ✅ | ✅ | ✅ |
| **Quản lý Nhân sự (`CRUD /employees`)** | ❌ | ❌ | ✅ | ✅ |
| **Nộp đơn xin nghỉ phép (`POST /leave-requests`)** | ✅ | ✅ | ✅ | ✅ |
| **Duyệt phép Cấp 1 (`approve-manager`)** | ❌ | ✅ *(Sếp trực tiếp)* | ❌ | ❌ |
| **Duyệt phép Cấp 2 (`approve-hr`)** | ❌ | ❌ | ✅ | ❌ |
| **Khởi tạo kỳ tính lương (`POST /payrolls/process`)** | ❌ | ❌ | ✅ | ❌ |
| **Xem phiếu lương của chính mình** | ✅ | ✅ | ✅ | ✅ |
| **Xem bảng lương toàn công ty (`GET /payrolls`)** | ❌ | ❌ | ✅ | ✅ |
| **Xem Database Audit Logs** | ❌ | ❌ | ❌ | ✅ |
