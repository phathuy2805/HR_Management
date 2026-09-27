import {
  Body,
  Controller,
  Get,
  Param,
  ParseIntPipe,
  Patch,
  Post,
} from '@nestjs/common';
import { Role } from '@prisma/client';
import { CurrentUser } from '../shared/decorators/current-user.decorator.js';
import { Roles } from '../shared/decorators/roles.decorator.js';
import { CreateLeaveRequestDto } from './dto/create-leave-request.dto.js';
import { LeaveRequestsService } from './leave-requests.service.js';

@Controller('leave-requests')
export class LeaveRequestsController {
  constructor(private readonly leaveService: LeaveRequestsService) {}

  @Post()
  create(
    @Body() body: CreateLeaveRequestDto,
    @CurrentUser('id') userId: number,
  ) {
    return this.leaveService.create(body, userId);
  }

  @Get('my-requests')
  getMyRequests(@CurrentUser('id') userId: number) {
    return this.leaveService.getMyRequests(userId);
  }

  @Roles(Role.MANAGER)
  @Patch(':id/approve-manager')
  approveByManager(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser('id') managerId: number,
  ) {
    return this.leaveService.approveByManager(id, managerId);
  }

  @Roles(Role.HR_MANAGER)
  @Patch(':id/approve-hr')
  approveByHr(
    @Param('id', ParseIntPipe) id: number,
    @CurrentUser('id') hrId: number,
  ) {
    return this.leaveService.approveByHr(id, hrId);
  }

  @Roles(Role.MANAGER, Role.HR_MANAGER)
  @Patch(':id/reject')
  reject(@Param('id', ParseIntPipe) id: number) {
    return this.leaveService.reject(id);
  }
}
