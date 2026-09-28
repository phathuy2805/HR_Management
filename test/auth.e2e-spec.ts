import { INestApplication } from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import request from 'supertest';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { AppModule } from '../src/app.module.js';

describe('Auth & Profile Flow (e2e)', () => {
  let app: INestApplication;
  const uniqueEmail = `test_e2e_${Date.now()}@example.com`;
  let accessToken: string;

  beforeAll(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await app.close();
  });

  it('1. Đăng ký tài khoản mới thành công (POST /auth/register)', async () => {
    const res = await request(app.getHttpServer())
      .post('/auth/register')
      .send({
        first_name: 'Nguyen',
        last_name: 'Van Test',
        email: uniqueEmail,
        password: 'password123',
        confirmPassword: 'password123',
      });

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.email).toBe(uniqueEmail);
    expect(res.body.data.password).toBeUndefined(); // Không để lộ password
  });

  it('2. Đăng nhập thành công và nhận được JWT Tokens (POST /auth/login)', async () => {
    const res = await request(app.getHttpServer())
      .post('/auth/login')
      .send({
        email: uniqueEmail,
        password: 'password123',
      });

    expect(res.status).toBe(201);
    expect(res.body.success).toBe(true);
    expect(res.body.data.access_token).toBeDefined();
    expect(res.body.data.refresh_token).toBeDefined();

    accessToken = res.body.data.access_token;
  });

  it('3. Truy cập Profile cá nhân thành công với Bearer Token (GET /profile)', async () => {
    const res = await request(app.getHttpServer())
      .get('/profile')
      .set('Authorization', `Bearer ${accessToken}`);

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data.email).toBe(uniqueEmail);
  });

  it('4. Chặn truy cập với Token giả mạo hoặc không hợp lệ (401 Unauthorized)', async () => {
    const res = await request(app.getHttpServer())
      .get('/profile')
      .set('Authorization', 'Bearer token_gia_mao_khong_hop_le');

    expect(res.status).toBe(401);
  });
});
