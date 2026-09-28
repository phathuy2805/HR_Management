import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseIntPipe,
  Patch,
  Post,
  Query,
} from '@nestjs/common';
import { ApiBearerAuth } from '@nestjs/swagger';
import { Role } from '@prisma/client';
import { CurrentUser } from '../shared/decorators/current-user.decorator.js';
import { Roles } from '../shared/decorators/roles.decorator.js';
import { CreateEmployeeDto } from './dto/create-employee.dto.js';
import { QueryEmployeeDto } from './dto/query-employee.dto.js';
import { UpdateEmployeeDto } from './dto/update-employee.dto.js';
import { EmployeesService } from './employees.service.js';

@ApiBearerAuth('JWT-auth')
@Controller('employees')
export class EmployeesController {
  constructor(private readonly employeesService: EmployeesService) {}

  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Post()
  create(@Body() body: CreateEmployeeDto) {
    return this.employeesService.create(body);
  }

  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Get()
  findAll(@Query() query: QueryEmployeeDto) {
    return this.employeesService.findAll(query);
  }

  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Get(':id')
  findOne(@Param('id', ParseIntPipe) id: number) {
    return this.employeesService.findOne(id);
  }

  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Patch(':id')
  update(
    @Param('id', ParseIntPipe) id: number,
    @Body() body: UpdateEmployeeDto,
    @CurrentUser('id') currentUserId: number,
  ) {
    return this.employeesService.update(id, body, currentUserId);
  }

  @Roles(Role.HR_MANAGER, Role.ADMIN)
  @Delete(':id')
  remove(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser('id') currentUserId: number,
  ) {
    return this.employeesService.remove(id, currentUserId);
  }
}
