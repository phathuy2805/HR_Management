import {
  BadRequestException,
  ForbiddenException,
  NotFoundException,
} from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { LeaveStatus, PayrollStatus, Role } from '@prisma/client';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { PayrollsRepository } from './payrolls.repository.js';
import { PayrollsService } from './payrolls.service.js';

describe('PayrollsService', () => {
  let service: PayrollsService;
  let repository: Partial<Record<keyof PayrollsRepository, any>>;

  beforeEach(async () => {
    repository = {
      findActiveEmployeesWithDetails: vi.fn(),
      findLeavesInPeriod: vi.fn(),
      createBatchPayrolls: vi.fn(),
      findAll: vi.fn(),
      findById: vi.fn(),
      findByEmployeeId: vi.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        PayrollsService,
        {
          provide: PayrollsRepository,
          useValue: repository,
        },
      ],
    }).compile();

    service = module.get<PayrollsService>(PayrollsService);
  });

  describe('processPayrolls', () => {
    it('ném lỗi BadRequestException nếu ngày kết thúc trước ngày bắt đầu kỳ lương', async () => {
      const dto = {
        pay_period_start: '2026-09-30',
        pay_period_end: '2026-09-01',
      };

      await expect(service.processPayrolls(dto, 1)).rejects.toThrow(
        BadRequestException,
      );
    });

    it('ném lỗi NotFoundException nếu không có nhân viên ACTIVE nào', async () => {
      const dto = {
        pay_period_start: '2026-09-01',
        pay_period_end: '2026-09-30',
      };

      repository.findActiveEmployeesWithDetails.mockResolvedValue([]);

      await expect(service.processPayrolls(dto, 1)).rejects.toThrow(
        NotFoundException,
      );
    });

    it('tính toán chính xác khấu trừ cho ngày nghỉ chưa duyệt và sinh bảng lương', async () => {
      const dto = {
        pay_period_start: '2026-09-01',
        pay_period_end: '2026-09-30',
      };

      const mockEmployee = {
        id: 1,
        job_title: { salary_range_min: 2200 }, // 2200 / 22 = 100/ngày
      };

      repository.findActiveEmployeesWithDetails.mockResolvedValue([mockEmployee]);

      // 1 đơn nghỉ 2 ngày nhưng chưa được APPROVED_BY_HR -> Bị trừ 2 ngày = 200
      repository.findLeavesInPeriod.mockResolvedValue([
        {
          start_date: new Date('2026-09-02'),
          end_date: new Date('2026-09-03'),
          status: LeaveStatus.PENDING, // Chưa duyệt
        },
      ]);

      repository.createBatchPayrolls.mockImplementation((data) =>
        Promise.resolve(data),
      );

      const result = await service.processPayrolls(dto, 99);
      expect(result).toHaveLength(1);
      expect(result[0].employee_id).toBe(1);
      expect(result[0].base_salary).toBe(2200);
      expect(result[0].deductions).toBe(200); // 2 ngày * 100
      expect(result[0].status).toBe(PayrollStatus.PENDING);
    });
  });

  describe('findOne', () => {
    it('ném lỗi NotFoundException nếu không tìm thấy phiếu lương', async () => {
      repository.findById.mockResolvedValue(null);

      await expect(
        service.findOne(999, { id: 1, role: Role.USER }),
      ).rejects.toThrow(NotFoundException);
    });

    it('ném lỗi ForbiddenException nếu nhân viên thường xem phiếu lương người khác', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        employee_id: 10, // Của nhân viên ID 10
      });

      await expect(
        service.findOne(1, { id: 99, role: Role.USER }), // Người đang xem là ID 99
      ).rejects.toThrow(ForbiddenException);
    });

    it('cho phép nhân viên xem phiếu lương của chính mình', async () => {
      const mockPayroll = { id: 1, employee_id: 10 };
      repository.findById.mockResolvedValue(mockPayroll);

      const result = await service.findOne(1, { id: 10, role: Role.USER });
      expect(result).toEqual(mockPayroll);
    });

    it('cho phép HR_MANAGER xem phiếu lương của bất kỳ ai', async () => {
      const mockPayroll = { id: 1, employee_id: 10 };
      repository.findById.mockResolvedValue(mockPayroll);

      const result = await service.findOne(1, {
        id: 99,
        role: Role.HR_MANAGER,
      });
      expect(result).toEqual(mockPayroll);
    });
  });
});
