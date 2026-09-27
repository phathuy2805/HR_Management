import {
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { hash } from 'bcrypt';
import { CreateEmployeeDto } from './dto/create-employee.dto.js';
import { QueryEmployeeDto } from './dto/query-employee.dto.js';
import { UpdateEmployeeDto } from './dto/update-employee.dto.js';
import { EmployeesRepository } from './employees.repository.js';

const SALT_ROUND = 10;
@Injectable()
export class EmployeesService {
  constructor(private readonly employeesRepo: EmployeesRepository) {}

  async getProfile(userId: number) {
    const employee = await this.employeesRepo.findById(userId);
    if (!employee) {
      throw new NotFoundException('Không tìm thấy thông tin nhân viên!');
    }
    return employee;
  }

  async create(body: CreateEmployeeDto) {
    const existing = await this.employeesRepo.findByEmail(body.email);
    if (existing) {
      throw new ConflictException('Email này đã tồn tại trong hệ thống!');
    }
    const hashedPassword = await hash(body.password, SALT_ROUND);
    return this.employeesRepo.create({
      first_name: body.first_name,
      last_name: body.last_name,
      email: body.email,
      password: hashedPassword,
      role: body.role,
      status: body.status,
      department: body.department_id
        ? { connect: { id: body.department_id } }
        : undefined,
      job_title: body.job_title_id
        ? { connect: { id: body.job_title_id } }
        : undefined,
      manager: body.manager_id
        ? { connect: { id: body.manager_id } }
        : undefined,
    });
  }

  async findAll(query: QueryEmployeeDto) {
    return this.employeesRepo.findAll(query);
  }

  async findOne(id: number) {
    const employee = await this.employeesRepo.findById(id);
    if (!employee) {
      throw new NotFoundException(`Không tìm thấy nhân viên có ID: ${id}`);
    }
    return employee;
  }

  async update(id: number, dto: UpdateEmployeeDto, actorId: number) {
    await this.findOne(id);
    if (dto.email) {
      const existing = await this.employeesRepo.findByEmail(dto.email);
      if (existing && existing.id !== id) {
        throw new ConflictException(
          'Email này đã được dùng bởi nhân viên khác!',
        );
      }
    }
    const updateData: any = {
      first_name: dto.first_name,
      last_name: dto.last_name,
      email: dto.email,
      role: dto.role,
      status: dto.status,
    };
    if (dto.password) {
      updateData.password = await hash(dto.password, SALT_ROUND);
    }
    if (dto.department_id !== undefined) {
      updateData.department = dto.department_id
        ? { connect: { id: dto.department_id } }
        : { disconnect: true };
    }
    if (dto.job_title_id !== undefined) {
      updateData.job_title = dto.job_title_id
        ? { connect: { id: dto.job_title_id } }
        : { disconnect: true };
    }
    if (dto.manager_id !== undefined) {
      updateData.manager = dto.manager_id
        ? { connect: { id: dto.manager_id } }
        : { disconnect: true };
    }
    return this.employeesRepo.updateWithAudit(id, updateData, actorId);
  }

  async remove(id: number, actorId: number) {
    await this.findOne(id);
    return this.employeesRepo.softDeleteWithAudit(id, actorId);
  }
}
