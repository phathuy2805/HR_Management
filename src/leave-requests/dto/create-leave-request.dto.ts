import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { LeaveType } from '@prisma/client';
import {
  IsDateString,
  IsEnum,
  IsNotEmpty,
  IsOptional,
  IsString,
} from 'class-validator';

export class CreateLeaveRequestDto {
  @ApiProperty({
    description: 'Ngày bắt đầu nghỉ (định dạng YYYY-MM-DD)',
    example: '2026-10-01',
  })
  @IsDateString({}, { message: 'start_date phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'Ngày bắt đầu không được để trống' })
  start_date: string;

  @ApiProperty({
    description: 'Ngày kết thúc nghỉ (định dạng YYYY-MM-DD, >= start_date)',
    example: '2026-10-03',
  })
  @IsDateString({}, { message: 'end_date phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'Ngày kết thúc không được để trống' })
  end_date: string;

  @ApiPropertyOptional({
    description: 'Loại nghỉ phép',
    enum: LeaveType,
    example: LeaveType.VACATION,
    default: LeaveType.CASUAL,
  })
  @IsOptional()
  @IsEnum(LeaveType, {
    message: 'Loại nghỉ phép không hợp lệ (SICK, CASUAL, VACATION)',
  })
  type?: LeaveType;

  @ApiPropertyOptional({
    description: 'Lý do xin nghỉ phép',
    example: 'Nghỉ phép thường niên cùng gia đình',
  })
  @IsOptional()
  @IsString()
  reason?: string;
}
