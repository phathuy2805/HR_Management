import { Module } from '@nestjs/common';
import { EmployeesController } from './employees.controller.js';
import { EmployeesRepository } from './employees.repository.js';
import { EmployeesService } from './employees.service.js';
import { ProfileController } from './profile.controller.js';

@Module({
  controllers: [EmployeesController, ProfileController],
  providers: [EmployeesService, EmployeesRepository],
  exports: [EmployeesService],
})
export class EmployeesModule {}
