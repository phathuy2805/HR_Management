import { Injectable } from '@nestjs/common';
import { EmployeeStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../shared/services/prisma.service.js';
import { QueryPayrollDto } from './dto/query-payroll.dto.js';

@Injectable()
export class PayrollsRepository {
  constructor(private readonly prisma: PrismaService) {}

  async findActiveEmployeesWithDetails() {
    return this.prisma.employee.findMany({
      where: { status: EmployeeStatus.ACTIVE },
      include: {
        job_title: true,
      },
    });
  }

  async findLeavesInPeriod(employeeId: number, startDate: Date, endDate: Date) {
    return this.prisma.leaveRequest.findMany({
      where: {
        employee_id: employeeId,
        start_date: { lte: endDate },
        end_date: { gte: startDate },
      },
    });
  }

  async createBatchPayrolls(
    payrollsData: Prisma.PayrollCreateManyInput[],
    actorId: number,
  ) {
    return this.prisma.$transaction(async (tx) => {
      await tx.$executeRawUnsafe(
        `SET LOCAL app.current_user_id = '${actorId}';`,
      );

      const createdPayrolls: any[] = [];
      for (const item of payrollsData) {
        const p = await tx.payroll.create({
          data: item,
          include: {
            employee: {
              select: {
                id: true,
                first_name: true,
                last_name: true,
                email: true,
              },
            },
          },
        });
        createdPayrolls.push(p);
      }
      return createdPayrolls;
    });
  }

  async findAll(query: QueryPayrollDto) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    const skip = (page - 1) * limit;

    const where: Prisma.PayrollWhereInput = {};
    if (query.employee_id) {
      where.employee_id = query.employee_id;
    }

    const [items, total] = await Promise.all([
      this.prisma.payroll.findMany({
        where,
        skip,
        take: limit,
        include: {
          employee: {
            select: {
              id: true,
              first_name: true,
              last_name: true,
              email: true,
            },
          },
        },
        orderBy: { id: 'desc' },
      }),
      this.prisma.payroll.count({ where }),
    ]);

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async findById(id: number) {
    return this.prisma.payroll.findUnique({
      where: { id },
      include: {
        employee: {
          select: {
            id: true,
            first_name: true,
            last_name: true,
            email: true,
            department: true,
            job_title: true,
          },
        },
      },
    });
  }

  async findByEmployeeId(employeeId: number, query: QueryPayrollDto) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    const skip = (page - 1) * limit;

    const where: Prisma.PayrollWhereInput = { employee_id: employeeId };

    const [items, total] = await Promise.all([
      this.prisma.payroll.findMany({
        where,
        skip,
        take: limit,
        orderBy: { id: 'desc' },
      }),
      this.prisma.payroll.count({ where }),
    ]);

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }
}
