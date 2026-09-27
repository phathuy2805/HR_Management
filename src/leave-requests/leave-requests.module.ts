import { Module } from '@nestjs/common';
import { LeaveRequestsController } from './leave-requests.controller.js';
import { LeaveRequestsRepository } from './leave-requests.repository.js';
import { LeaveRequestsService } from './leave-requests.service.js';

@Module({
  controllers: [LeaveRequestsController],
  providers: [LeaveRequestsService, LeaveRequestsRepository],
  exports: [LeaveRequestsService],
})
export class LeaveRequestsModule {}
