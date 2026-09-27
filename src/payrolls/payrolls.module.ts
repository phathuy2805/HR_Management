import { Module } from '@nestjs/common';
import { PayrollsController } from './payrolls.controller.js';
import { PayrollsRepository } from './payrolls.repository.js';
import { PayrollsService } from './payrolls.service.js';

@Module({
  controllers: [PayrollsController],
  providers: [PayrollsService, PayrollsRepository],
  exports: [PayrollsService],
})
export class PayrollsModule {}
