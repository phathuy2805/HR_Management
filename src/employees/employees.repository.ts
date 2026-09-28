import { Injectable } from '@nestjs/common';
import { Employee, EmployeeStatus, Prisma } from '@prisma/client';
import { PrismaService } from '../shared/services/prisma.service.js';
import { QueryEmployeeDto } from './dto/query-employee.dto.js';

@Injectable()
export class EmployeesRepository {
  constructor(private readonly prisma: PrismaService) {}

  async findById(id: number): Promise<Omit<Employee, 'password'> | null> {
    return this.prisma.employee.findUnique({
      where: { id },
      omit: { password: true },
      include: {
        department: true,
        job_title: true,
        manager: {
          select: { id: true, first_name: true, last_name: true, email: true },
        },
      },
    });
  }

  async findByEmail(email: string): Promise<Employee | null> {
    return this.prisma.employee.findUnique({
      where: { email },
    });
  }

  async createWithAudit(
    data: Prisma.EmployeeCreateInput,
    actorId: number,
  ): Promise<Omit<Employee, 'password'>> {
    return this.prisma.$transaction(async (tx) => {
      await tx.$executeRawUnsafe(
        `SET LOCAL app.current_user_id = '${actorId}';`,
      );
      return tx.employee.create({
        data,
        omit: { password: true },
      });
    });
  }

  async findAll(query: QueryEmployeeDto) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    const skip = (page - 1) * limit;

    const where: Prisma.EmployeeWhereInput = {};

    if (query.department_id) {
      where.department_id = query.department_id;
    }

    if (query.search) {
      where.OR = [
        { first_name: { contains: query.search, mode: 'insensitive' } },
        { last_name: { contains: query.search, mode: 'insensitive' } },
        { email: { contains: query.search, mode: 'insensitive' } },
      ];
    }

    const [items, total] = await Promise.all([
      this.prisma.employee.findMany({
        where,
        skip,
        take: limit,
        omit: { password: true },
        include: {
          department: { select: { id: true, name: true } },
          job_title: { select: { id: true, title: true } },
        },
        orderBy: { id: 'desc' },
      }),
      this.prisma.employee.count({ where }),
    ]);

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async updateWithAudit(
    id: number,
    data: Prisma.EmployeeUpdateInput,
    actorId: number,
  ): Promise<Omit<Employee, 'password'>> {
    return this.prisma.$transaction(async (tx) => {
      await tx.$executeRawUnsafe(
        `SET LOCAL app.current_user_id = '${actorId}';`,
      );

      return tx.employee.update({
        where: { id },
        data,
        omit: { password: true },
      });
    });
  }

  async softDeleteWithAudit(id: number, actorId: number) {
    return this.prisma.$transaction(async (tx) => {
      await tx.$executeRawUnsafe(
        `SET LOCAL app.current_user_id = '${actorId}';`,
      );

      return tx.employee.update({
        where: { id },
        data: { status: EmployeeStatus.TERMINATED },
        omit: { password: true },
      });
    });
  }
}
