-- CreateEnum
CREATE TYPE "Role" AS ENUM ('USER', 'MANAGER', 'HR_MANAGER', 'ADMIN');

-- CreateEnum
CREATE TYPE "EmployeeStatus" AS ENUM ('ACTIVE', 'INACTIVE', 'TERMINATED');

-- CreateEnum
CREATE TYPE "LeaveType" AS ENUM ('SICK', 'CASUAL', 'VACATION');

-- CreateEnum
CREATE TYPE "LeaveStatus" AS ENUM ('PENDING', 'APPROVED_BY_MANAGER', 'APPROVED_BY_HR', 'REJECTED');

-- CreateEnum
CREATE TYPE "PayrollStatus" AS ENUM ('PENDING', 'PAID');

-- CreateTable
CREATE TABLE "departments" (
    "id" SERIAL NOT NULL,
    "name" VARCHAR(100) NOT NULL,
    "budget" DECIMAL(12,2),
    "location" VARCHAR(150) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "departments_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "job_titles" (
    "id" SERIAL NOT NULL,
    "title" VARCHAR(100) NOT NULL,
    "salary_range_min" DECIMAL(10,2),
    "salary_range_max" DECIMAL(10,2),

    CONSTRAINT "job_titles_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "employees" (
    "id" SERIAL NOT NULL,
    "first_name" VARCHAR(50) NOT NULL,
    "last_name" VARCHAR(50) NOT NULL,
    "email" VARCHAR(150) NOT NULL,
    "password" VARCHAR(255) NOT NULL,
    "role" "Role" NOT NULL DEFAULT 'USER',
    "department_id" INTEGER,
    "job_title_id" INTEGER,
    "manager_id" INTEGER,
    "status" "EmployeeStatus" NOT NULL DEFAULT 'ACTIVE',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "employees_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "leave_requests" (
    "id" SERIAL NOT NULL,
    "employee_id" INTEGER NOT NULL,
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "type" "LeaveType" NOT NULL DEFAULT 'CASUAL',
    "status" "LeaveStatus" NOT NULL DEFAULT 'PENDING',
    "reason" TEXT,
    "approved_by_manager_id" INTEGER,
    "approved_by_hr_id" INTEGER,

    CONSTRAINT "leave_requests_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "payrolls" (
    "id" SERIAL NOT NULL,
    "employee_id" INTEGER NOT NULL,
    "base_salary" DECIMAL(10,2) NOT NULL,
    "bonuses" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "deductions" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "total_salary" NUMERIC(10, 2) GENERATED ALWAYS AS (base_salary + bonuses - deductions) STORED,
    "pay_period_start" DATE NOT NULL,
    "pay_period_end" DATE NOT NULL,
    "status" "PayrollStatus" NOT NULL DEFAULT 'PENDING',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "payrolls_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "audit_logs" (
    "id" BIGSERIAL NOT NULL,
    "actor_id" INTEGER,
    "action" VARCHAR(20) NOT NULL,
    "table_name" VARCHAR(50) NOT NULL,
    "record_id" INTEGER NOT NULL,
    "old_value" JSONB,
    "new_value" JSONB,
    "ip_address" VARCHAR(45),
    "timestamp" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "departments_name_key" ON "departments"("name");

-- CreateIndex
CREATE UNIQUE INDEX "job_titles_title_key" ON "job_titles"("title");

-- CreateIndex
CREATE UNIQUE INDEX "employees_email_key" ON "employees"("email");

-- AddForeignKey
ALTER TABLE "employees" ADD CONSTRAINT "employees_department_id_fkey" FOREIGN KEY ("department_id") REFERENCES "departments"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "employees" ADD CONSTRAINT "employees_manager_id_fkey" FOREIGN KEY ("manager_id") REFERENCES "employees"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "employees" ADD CONSTRAINT "employees_job_title_id_fkey" FOREIGN KEY ("job_title_id") REFERENCES "job_titles"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "leave_requests" ADD CONSTRAINT "leave_requests_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "employees"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "leave_requests" ADD CONSTRAINT "leave_requests_approved_by_manager_id_fkey" FOREIGN KEY ("approved_by_manager_id") REFERENCES "employees"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "leave_requests" ADD CONSTRAINT "leave_requests_approved_by_hr_id_fkey" FOREIGN KEY ("approved_by_hr_id") REFERENCES "employees"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "payrolls" ADD CONSTRAINT "payrolls_employee_id_fkey" FOREIGN KEY ("employee_id") REFERENCES "employees"("id") ON DELETE CASCADE ON UPDATE CASCADE;


ALTER TABLE "departments" ADD CONSTRAINT "chk_department_budget" CHECK (budget >= 0);
ALTER TABLE "job_titles" ADD CONSTRAINT "chk_job_title_min_salary" CHECK (salary_range_min > 0);
ALTER TABLE "job_titles" ADD CONSTRAINT "chk_job_title_salary_range" CHECK (salary_range_max >= salary_range_min);
ALTER TABLE "leave_requests" ADD CONSTRAINT "chk_leave_dates" CHECK (end_date >= start_date);
ALTER TABLE "payrolls" ADD CONSTRAINT "chk_payroll_base_salary" CHECK (base_salary > 0);
ALTER TABLE "payrolls" ADD CONSTRAINT "chk_payroll_bonuses" CHECK (bonuses >= 0);
ALTER TABLE "payrolls" ADD CONSTRAINT "chk_payroll_deductions" CHECK (deductions >= 0);


CREATE OR REPLACE FUNCTION process_audit_log()
RETURNS TRIGGER AS $$
DECLARE
    v_actor_id INT;
    v_record_id INT;
    v_old_value JSONB := NULL;
    v_new_value JSONB := NULL;
    v_actor_str TEXT;
BEGIN
    v_actor_str := NULLIF(current_setting('app.current_user_id', true), '');
    IF v_actor_str IS NOT NULL THEN
        v_actor_id := v_actor_str::INT;
    ELSE
        v_actor_id := NULL;
    END IF;

    IF (TG_OP = 'INSERT') THEN
        v_record_id := NEW.id;
        v_new_value := to_jsonb(NEW);
    ELSIF (TG_OP = 'UPDATE') THEN
        v_record_id := NEW.id;
        v_old_value := to_jsonb(OLD);
        v_new_value := to_jsonb(NEW);
    ELSIF (TG_OP = 'DELETE') THEN
        v_record_id := OLD.id;
        v_old_value := to_jsonb(OLD);
    END IF;


    INSERT INTO "audit_logs" ("actor_id", "action", "table_name", "record_id", "old_value", "new_value", "timestamp")
    VALUES (v_actor_id, TG_OP, TG_TABLE_NAME, v_record_id, v_old_value, v_new_value, NOW());

    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_audit_employees
AFTER INSERT OR UPDATE OR DELETE ON "employees"
FOR EACH ROW
EXECUTE FUNCTION process_audit_log();

CREATE TRIGGER trg_audit_payrolls
AFTER INSERT OR UPDATE OR DELETE ON "payrolls"
FOR EACH ROW
EXECUTE FUNCTION process_audit_log();