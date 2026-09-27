import { EmployeeStatus, Role } from '@prisma/client';
import { Type } from 'class-transformer';
import {
  IsEmail,
  IsEnum,
  IsInt,
  IsNotEmpty,
  IsOptional,
  IsString,
  MinLength,
} from 'class-validator';

export class CreateEmployeeDto {
  @IsString()
  @IsNotEmpty({ message: 'Họ không được trống' })
  first_name: string;

  @IsString()
  @IsNotEmpty({ message: 'Tên không được trống' })
  last_name: string;

  @IsEmail({}, { message: 'Email không đúng định dạng' })
  @IsNotEmpty({ message: 'Email không được trống' })
  email: string;

  @IsString()
  @MinLength(6, { message: 'Mật khẩu phải từ 6 ký tự' })
  @IsNotEmpty({ message: 'Mật khẩu không được trống' })
  password: string;

  @IsOptional()
  @IsEnum(Role, { message: 'Role không hợp lệ' })
  role?: Role;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  department_id?: number;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  job_title_id?: number;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  manager_id?: number;

  @IsOptional()
  @IsEnum(EmployeeStatus, { message: 'Trạng thái không hợp lệ' })
  status?: EmployeeStatus;
}
