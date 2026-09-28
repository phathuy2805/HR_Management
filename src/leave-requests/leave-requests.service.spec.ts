import {
  BadRequestException,
  ForbiddenException,
  NotFoundException,
} from '@nestjs/common';
import { Test, TestingModule } from '@nestjs/testing';
import { LeaveStatus, LeaveType } from '@prisma/client';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LeaveRequestsRepository } from './leave-requests.repository.js';
import { LeaveRequestsService } from './leave-requests.service.js';

describe('LeaveRequestsService', () => {
  let service: LeaveRequestsService;
  let repository: Partial<Record<keyof LeaveRequestsRepository, any>>;

  beforeEach(async () => {
    repository = {
      create: vi.fn(),
      findById: vi.fn(),
      findByEmployeeId: vi.fn(),
      updateStatus: vi.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        LeaveRequestsService,
        {
          provide: LeaveRequestsRepository,
          useValue: repository,
        },
      ],
    }).compile();

    service = module.get<LeaveRequestsService>(LeaveRequestsService);
  });

  describe('create', () => {
    it('ném lỗi BadRequestException nếu ngày kết thúc trước ngày bắt đầu', async () => {
      const dto = {
        start_date: '2026-09-10',
        end_date: '2026-09-01',
        type: LeaveType.SICK,
      };

      await expect(service.create(dto, 1)).rejects.toThrow(
        BadRequestException,
      );
    });

    it('tạo đơn thành công với trạng thái PENDING', async () => {
      const dto = {
        start_date: '2026-09-01',
        end_date: '2026-09-05',
        type: LeaveType.VACATION,
        reason: 'Đi du lịch',
      };

      const expectedResult = { id: 1, ...dto, status: LeaveStatus.PENDING };
      repository.create.mockResolvedValue(expectedResult);

      const result = await service.create(dto, 1);
      expect(result).toEqual(expectedResult);
      expect(repository.create).toHaveBeenCalled();
    });
  });

  describe('approveByManager', () => {
    it('ném lỗi NotFoundException nếu không tìm thấy đơn', async () => {
      repository.findById.mockResolvedValue(null);
      await expect(service.approveByManager(999, 10)).rejects.toThrow(
        NotFoundException,
      );
    });

    it('ném lỗi BadRequestException nếu đơn không ở trạng thái PENDING', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.APPROVED_BY_MANAGER,
        employee: { manager_id: 10 },
      });

      await expect(service.approveByManager(1, 10)).rejects.toThrow(
        BadRequestException,
      );
    });

    it('ném lỗi ForbiddenException nếu người duyệt không phải là sếp trực tiếp', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.PENDING,
        employee: { manager_id: 99 }, // Sếp là 99, nhưng người gọi là 10
      });

      await expect(service.approveByManager(1, 10)).rejects.toThrow(
        ForbiddenException,
      );
    });

    it('duyệt thành công Cấp 1 khi đúng sếp trực tiếp', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.PENDING,
        employee: { manager_id: 10 },
      });

      const updatedLeave = {
        id: 1,
        status: LeaveStatus.APPROVED_BY_MANAGER,
        approved_by_manager_id: 10,
      };
      repository.updateStatus.mockResolvedValue(updatedLeave);

      const result = await service.approveByManager(1, 10);
      expect(result.status).toBe(LeaveStatus.APPROVED_BY_MANAGER);
      expect(repository.updateStatus).toHaveBeenCalledWith(1, {
        status: LeaveStatus.APPROVED_BY_MANAGER,
        approved_by_manager_id: 10,
      });
    });
  });

  describe('approveByHr', () => {
    it('ném lỗi BadRequestException nếu đơn chưa qua Cấp 1 phê duyệt', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.PENDING, // Mới ở PENDING, chưa qua APPROVED_BY_MANAGER
      });

      await expect(service.approveByHr(1, 20)).rejects.toThrow(
        BadRequestException,
      );
    });

    it('duyệt thành công Cấp 2 khi đơn đã qua Cấp 1', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.APPROVED_BY_MANAGER,
      });

      const updatedLeave = {
        id: 1,
        status: LeaveStatus.APPROVED_BY_HR,
        approved_by_hr_id: 20,
      };
      repository.updateStatus.mockResolvedValue(updatedLeave);

      const result = await service.approveByHr(1, 20);
      expect(result.status).toBe(LeaveStatus.APPROVED_BY_HR);
      expect(repository.updateStatus).toHaveBeenCalledWith(1, {
        status: LeaveStatus.APPROVED_BY_HR,
        approved_by_hr_id: 20,
      });
    });
  });

  describe('reject', () => {
    it('ném lỗi BadRequestException nếu đơn đã kết thúc quy trình', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.APPROVED_BY_HR,
      });

      await expect(service.reject(1)).rejects.toThrow(BadRequestException);
    });

    it('từ chối đơn thành công', async () => {
      repository.findById.mockResolvedValue({
        id: 1,
        status: LeaveStatus.PENDING,
      });

      repository.updateStatus.mockResolvedValue({
        id: 1,
        status: LeaveStatus.REJECTED,
      });

      const result = await service.reject(1);
      expect(result.status).toBe(LeaveStatus.REJECTED);
    });
  });
});
