import { Controller, Get } from '@nestjs/common';
import { CurrentUser } from '../shared/decorators/current-user.decorator.js';
import { EmployeesService } from './employees.service.js';

@Controller('profile')
export class ProfileController {
  constructor(private readonly employeesService: EmployeesService) {}
  @Get()
  getProfile(@CurrentUser('id') userId: number) {
    return this.employeesService.getProfile(userId);
  }
}
