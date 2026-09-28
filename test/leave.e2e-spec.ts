import { INestApplication } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { LeaveStatus, LeaveType, Role } from '@prisma/client';
import request from 'supertest';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { AppModule } from '../src/app.module.js';
import { PrismaService } from '../src/shared/services/prisma.service.js';

describe('Leave Request Dual-Approval Workflow (e2e)', () => {
  let app: INestApplication;
  let prisma: PrismaService;

  let employeeToken: string;
  let managerToken: string;
  let hrToken: string;

  let managerId: number;
  let leaveRequestId: number;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
    prisma = app.get<PrismaService>(PrismaService);

    const managerRes = await request(app.getHttpServer())
      .post('/auth/register')
      .send({
        first_name: 'Manager',
        last_name: 'One',
        email: `mgr_${Date.now()}@example.com`,
        password: 'password123',
        confirm_password: 'password123',
      });
    managerId = managerRes.body.data.id;
    await prisma.employee.update({
      where: { id: managerId },
      data: { role: Role.MANAGER },
    });
    const mgrLogin = await request(app.getHttpServer())
      .post('/auth/login')
      .send({
        email: managerRes.body.data.email,
        password: 'password123',
      });
    managerToken = mgrLogin.body.data.access_token;

    const hrRes = await request(app.getHttpServer())
      .post('/auth/register')
      .send({
        first_name: 'HR',
        last_name: 'Lead',
        email: `hr_${Date.now()}@example.com`,
        password: 'password123',
        confirm_password: 'password123',
      });
    const hrId = hrRes.body.data.id;
    await prisma.employee.update({
      where: { id: hrId },
      data: { role: Role.HR_MANAGER },
    });
    const hrLogin = await request(app.getHttpServer())
      .post('/auth/login')
      .send({
        email: hrRes.body.data.email,
        password: 'password123',
      });
    hrToken = hrLogin.body.data.access_token;

    const empRes = await request(app.getHttpServer())
      .post('/auth/register')
      .send({
        first_name: 'Staff',
        last_name: 'Member',
        email: `staff_${Date.now()}@example.com`,
        password: 'password123',
        confirm_password: 'password123',
      });
    const empId = empRes.body.data.id;
    await prisma.employee.update({
      where: { id: empId },
      data: { manager_id: managerId },
    });
    const empLogin = await request(app.getHttpServer())
      .post('/auth/login')
      .send({
        email: empRes.body.data.email,
        password: 'password123',
      });
    employeeToken = empLogin.body.data.access_token;
  });

  afterAll(async () => {
    await app.close();
  });

  it('1. Nhân viên nộp đơn xin nghỉ phép (POST /leave-requests)', async () => {
    const res = await request(app.getHttpServer())
      .post('/leave-requests')
      .set('Authorization', `Bearer ${employeeToken}`)
      .send({
        start_date: '2026-10-01',
        end_date: '2026-10-03',
        type: LeaveType.VACATION,
        reason: 'Nghỉ phép thường niên',
      });

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.status).toBe(LeaveStatus.PENDING);

    leaveRequestId = res.body.data.id;
  });

  it('2. Manager trực tiếp duyệt Cấp 1 (PATCH /leave-requests/:id/approve-manager)', async () => {
    const res = await request(app.getHttpServer())
      .patch(`/leave-requests/${leaveRequestId}/approve-manager`)
      .set('Authorization', `Bearer ${managerToken}`);

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.status).toBe(LeaveStatus.APPROVED_BY_MANAGER);
    expect(res.body.data.approved_by_manager_id).toBe(managerId);
  });

  it('3. HR Manager duyệt Cấp 2 cuối cùng (PATCH /leave-requests/:id/approve-hr)', async () => {
    const res = await request(app.getHttpServer())
      .patch(`/leave-requests/${leaveRequestId}/approve-hr`)
      .set('Authorization', `Bearer ${hrToken}`);

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.status).toBe(LeaveStatus.APPROVED_BY_HR);
    expect(res.body.data.approved_by_hr_id).toBeDefined();
  });
});
