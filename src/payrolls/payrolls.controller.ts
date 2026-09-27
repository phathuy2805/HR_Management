import {
  Body,
  Controller,
  Get,
  Param,
  ParseIntPipe,
  Post,
  Query,
} from '@nestjs/common';
import { Role } from '@prisma/client';
import { CurrentUser } from '../shared/decorators/current-user.decorator.js';
import { Roles } from '../shared/decorators/roles.decorator.js';
import { ProcessPayrollDto } from './dto/process-payroll.dto.js';
import { QueryPayrollDto } from './dto/query-payroll.dto.js';
import { PayrollsService } from './payrolls.service.js';

@Controller('payrolls')
export class PayrollsController {
  constructor(private readonly payrollsService: PayrollsService) {}

  // 1. Khởi tạo bảng lương tháng (Chỉ dành riêng cho HR_MANAGER - Mục 4.4.1 SRS)
  @Roles(Role.HR_MANAGER)
  @Post('process')
  processPayrolls(
    @Body() body: ProcessPayrollDto,
    @CurrentUser('id') actorId: number,
  ) {
    return this.payrollsService.processPayrolls(body, actorId);
  }

  // 2. Nhân viên tự xem danh sách phiếu lương của bản thân (Mục 4.4.2 SRS)
  @Get('my-payrolls')
  getMyPayrolls(
    @CurrentUser('id') userId: number,
    @Query() query: QueryPayrollDto,
  ) {
    return this.payrollsService.getMyPayrolls(userId, query);
  }

  // 3. Xem danh sách toàn bộ phiếu lương công ty (Chỉ HR_MANAGER và ADMIN)
  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Get()
  findAll(@Query() query: QueryPayrollDto) {
    return this.payrollsService.findAll(query);
  }

  // 4. Xem chi tiết 1 phiếu lương (Phân quyền kiểm tra ở Service)
  @Get(':id')
  findOne(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser() currentUser: { id: number; role: Role },
  ) {
    return this.payrollsService.findOne(id, currentUser);
  }
}
