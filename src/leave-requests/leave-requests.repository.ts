import { Injectable } from '@nestjs/common';
import { LeaveStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../shared/services/prisma.service.js';

@Injectable()
export class LeaveRequestsRepository {
  constructor(private readonly prisma: PrismaService) {}

  async create(data: Prisma.LeaveRequestCreateInput) {
    return this.prisma.leaveRequest.create({ data });
  }

  async findById(id: number) {
    return this.prisma.leaveRequest.findUnique({
      where: { id },
      include: {
        employee: {
          select: {
            id: true,
            first_name: true,
            last_name: true,
            email: true,
            manager_id: true,
          },
        },
      },
    });
  }

  async findByEmployeeId(employeeId: number) {
    return this.prisma.leaveRequest.findMany({
      where: { employee_id: employeeId },
      orderBy: { id: 'desc' },
    });
  }

  async updateStatus(
    id: number,
    data: {
      status: LeaveStatus;
      approved_by_manager_id?: number;
      approved_by_hr_id?: number;
    },
  ) {
    return this.prisma.leaveRequest.update({
      where: { id },
      data,
    });
  }
}
