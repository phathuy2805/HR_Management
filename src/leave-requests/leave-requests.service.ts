import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { LeaveStatus } from '@prisma/client';
import { CreateLeaveRequestDto } from './dto/create-leave-request.dto.js';
import { LeaveRequestsRepository } from './leave-requests.repository.js';

@Injectable()
export class LeaveRequestsService {
  constructor(private readonly leaveRepo: LeaveRequestsRepository) {}

  async create(dto: CreateLeaveRequestDto, employeeId: number) {
    const startDate = new Date(dto.start_date);
    const endDate = new Date(dto.end_date);

    if (endDate < startDate) {
      throw new BadRequestException(
        'Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu!',
      );
    }

    return this.leaveRepo.create({
      start_date: startDate,
      end_date: endDate,
      type: dto.type,
      reason: dto.reason,
      status: LeaveStatus.PENDING,
      employee: { connect: { id: employeeId } },
    });
  }

  async getMyRequests(employeeId: number) {
    return this.leaveRepo.findByEmployeeId(employeeId);
  }

  async approveByManager(id: number, managerId: number) {
    const leave = await this.leaveRepo.findById(id);
    if (!leave) {
      throw new NotFoundException('Không tìm thấy đơn xin nghỉ phép!');
    }

    if (leave.status !== LeaveStatus.PENDING) {
      throw new BadRequestException(
        'Đơn này không ở trạng thái chờ duyệt cấp 1!',
      );
    }

    if (leave.employee.manager_id !== managerId) {
      throw new ForbiddenException(
        'Bạn không phải là quản lý trực tiếp của nhân viên này!',
      );
    }

    return this.leaveRepo.updateStatus(id, {
      status: LeaveStatus.APPROVED_BY_MANAGER,
      approved_by_manager_id: managerId,
    });
  }

  async approveByHr(id: number, hrId: number) {
    const leave = await this.leaveRepo.findById(id);
    if (!leave) {
      throw new NotFoundException('Không tìm thấy đơn xin nghỉ phép!');
    }

    if (leave.status !== LeaveStatus.APPROVED_BY_MANAGER) {
      throw new BadRequestException(
        'Đơn xin nghỉ phép này chưa được Quản lý trực tiếp phê duyệt!',
      );
    }

    return this.leaveRepo.updateStatus(id, {
      status: LeaveStatus.APPROVED_BY_HR,
      approved_by_hr_id: hrId,
    });
  }

  async reject(id: number) {
    const leave = await this.leaveRepo.findById(id);
    if (!leave) {
      throw new NotFoundException('Không tìm thấy đơn xin nghỉ phép!');
    }

    if (
      leave.status === LeaveStatus.REJECTED ||
      leave.status === LeaveStatus.APPROVED_BY_HR
    ) {
      throw new BadRequestException(
        'Không thể từ chối đơn đã hoàn tất quy trình!',
      );
    }

    return this.leaveRepo.updateStatus(id, {
      status: LeaveStatus.REJECTED,
    });
  }
}
