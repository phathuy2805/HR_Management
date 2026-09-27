import { Injectable } from '@nestjs/common';
import { Employee } from '@prisma/client';
import { PrismaService } from '../shared/services/prisma.service.js';
import { CreateEmployeeBodyType } from './auth.type.js';

@Injectable()
export class AuthRepository {
  constructor(private readonly prisma: PrismaService) {}
  register(
    body: CreateEmployeeBodyType,
  ): Promise<Omit<Employee, 'password'> | null> {
    return this.prisma.employee.create({
      data: {
        ...body,
      },
      omit: {
        password: true,
      },
    });
  }
}
