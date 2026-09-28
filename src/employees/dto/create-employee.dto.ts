import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
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
  @ApiProperty({
    description: 'Họ của nhân viên',
    example: 'Tran',
  })
  @IsString()
  @IsNotEmpty({ message: 'Họ không được trống' })
  first_name: string;

  @ApiProperty({
    description: 'Tên của nhân viên',
    example: 'Van B',
  })
  @IsString()
  @IsNotEmpty({ message: 'Tên không được trống' })
  last_name: string;

  @ApiProperty({
    description: 'Email duy nhất của nhân viên',
    example: 'vanb@company.com',
  })
  @IsEmail({}, { message: 'Email không đúng định dạng' })
  @IsNotEmpty({ message: 'Email không được trống' })
  email: string;

  @ApiProperty({
    description: 'Mật khẩu tài khoản (tối thiểu 6 ký tự)',
    example: 'password123',
    minLength: 6,
  })
  @IsString()
  @MinLength(6, { message: 'Mật khẩu phải từ 6 ký tự' })
  @IsNotEmpty({ message: 'Mật khẩu không được trống' })
  password: string;

  @ApiPropertyOptional({
    description: 'Phân quyền trong hệ thống',
    enum: Role,
    example: Role.USER,
  })
  @IsOptional()
  @IsEnum(Role, { message: 'Role không hợp lệ' })
  role?: Role;

  @ApiPropertyOptional({
    description: 'ID phòng ban làm việc',
    example: 1,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  department_id?: number;

  @ApiPropertyOptional({
    description: 'ID chức danh công việc',
    example: 1,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  job_title_id?: number;

  @ApiPropertyOptional({
    description: 'ID người quản lý trực tiếp (Manager)',
    example: 2,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  manager_id?: number;

  @ApiPropertyOptional({
    description: 'Trạng thái hoạt động của nhân sự',
    enum: EmployeeStatus,
    example: EmployeeStatus.ACTIVE,
  })
  @IsOptional()
  @IsEnum(EmployeeStatus, { message: 'Trạng thái không hợp lệ' })
  status?: EmployeeStatus;
}
