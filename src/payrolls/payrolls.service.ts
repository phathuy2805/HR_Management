import {
  BadRequestException,
  ForbiddenException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { LeaveStatus, PayrollStatus, Role } from '@prisma/client';
import { ProcessPayrollDto } from './dto/process-payroll.dto.js';
import { QueryPayrollDto } from './dto/query-payroll.dto.js';
import { PayrollsRepository } from './payrolls.repository.js';

@Injectable()
export class PayrollsService {
  constructor(private readonly payrollsRepo: PayrollsRepository) {}

  async processPayrolls(dto: ProcessPayrollDto, actorId: number) {
    const startDate = new Date(dto.pay_period_start);
    const endDate = new Date(dto.pay_period_end);

    if (endDate < startDate) {
      throw new BadRequestException(
        'pay_period_end phải lớn hơn hoặc bằng pay_period_start!',
      );
    }

    const activeEmployees =
      await this.payrollsRepo.findActiveEmployeesWithDetails();

    if (!activeEmployees || activeEmployees.length === 0) {
      throw new NotFoundException(
        'Không có nhân viên nào đang hoạt động để tính lương!',
      );
    }

    const payrollsToCreate: any[] = [];

    for (const emp of activeEmployees) {
      const baseSalary = emp.job_title?.salary_range_min
        ? Number(emp.job_title.salary_range_min)
        : 1000;

      const leaves = await this.payrollsRepo.findLeavesInPeriod(
        emp.id,
        startDate,
        endDate,
      );

      let invalidLeaveDays = 0;
      for (const leave of leaves) {
        if (leave.status !== LeaveStatus.APPROVED_BY_HR) {
          const lStart = new Date(leave.start_date);
          const lEnd = new Date(leave.end_date);

          const overlapStart = Math.max(lStart.getTime(), startDate.getTime());
          const overlapEnd = Math.min(lEnd.getTime(), endDate.getTime());

          if (overlapEnd >= overlapStart) {
            const days =
              Math.ceil((overlapEnd - overlapStart) / (1000 * 60 * 60 * 24)) + 1;
            invalidLeaveDays += days;
          }
        }
      }

      const dailyRate = baseSalary / 22;
      const deductions = Math.min(
        Number((invalidLeaveDays * dailyRate).toFixed(2)),
        baseSalary,
      );

      payrollsToCreate.push({
        employee_id: emp.id,
        base_salary: baseSalary,
        bonuses: 0,
        deductions,
        pay_period_start: startDate,
        pay_period_end: endDate,
        status: PayrollStatus.PENDING,
      });
    }

    return this.payrollsRepo.createBatchPayrolls(payrollsToCreate, actorId);
  }

  async findAll(query: QueryPayrollDto) {
    return this.payrollsRepo.findAll(query);
  }

  async getMyPayrolls(employeeId: number, query: QueryPayrollDto) {
    return this.payrollsRepo.findByEmployeeId(employeeId, query);
  }

  async findOne(id: number, currentUser: { id: number; role: Role }) {
    const payroll = await this.payrollsRepo.findById(id);
    if (!payroll) {
      throw new NotFoundException(`Không tìm thấy phiếu lương có ID: ${id}`);
    }

    if (
      currentUser.role !== Role.ADMIN &&
      currentUser.role !== Role.HR_MANAGER
    ) {
      if (payroll.employee_id !== currentUser.id) {
        throw new ForbiddenException(
          'Bạn không có quyền xem phiếu lương của người khác!',
        );
      }
    }

    return payroll;
  }
}
