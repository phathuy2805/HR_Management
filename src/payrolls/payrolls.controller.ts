import {
  Body,
  Controller,
  Get,
  Param,
  ParseIntPipe,
  Post,
  Query,
} from '@nestjs/common';
import { ApiBearerAuth } from '@nestjs/swagger';
import { Role } from '@prisma/client';
import { CurrentUser } from '../shared/decorators/current-user.decorator.js';
import { Roles } from '../shared/decorators/roles.decorator.js';
import { ProcessPayrollDto } from './dto/process-payroll.dto.js';
import { QueryPayrollDto } from './dto/query-payroll.dto.js';
import { PayrollsService } from './payrolls.service.js';

@ApiBearerAuth('JWT-auth')
@Controller('payrolls')
export class PayrollsController {
  constructor(private readonly payrollsService: PayrollsService) {}

  @Roles(Role.HR_MANAGER)
  @Post('process')
  processPayrolls(
    @Body() body: ProcessPayrollDto,
    @CurrentUser('id') actorId: number,
  ) {
    return this.payrollsService.processPayrolls(body, actorId);
  }

  @Get('my-payrolls')
  getMyPayrolls(
    @CurrentUser('id') userId: number,
    @Query() query: QueryPayrollDto,
  ) {
    return this.payrollsService.getMyPayrolls(userId, query);
  }

  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Get()
  findAll(@Query() query: QueryPayrollDto) {
    return this.payrollsService.findAll(query);
  }

  @Get(':id')
  findOne(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser() currentUser: { id: number; role: Role },
  ) {
    return this.payrollsService.findOne(id, currentUser);
  }
}
