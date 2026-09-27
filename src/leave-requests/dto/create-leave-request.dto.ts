import { IsDateString, IsEnum, IsNotEmpty, IsOptional, IsString } from 'class-validator';
import { LeaveType } from '@prisma/client';

export class CreateLeaveRequestDto {
  @IsDateString({}, { message: 'start_date phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'Ngày bắt đầu không được để trống' })
  start_date: string;

  @IsDateString({}, { message: 'end_date phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'Ngày kết thúc không được để trống' })
  end_date: string;

  @IsOptional()
  @IsEnum(LeaveType, {
    message: 'Loại nghỉ phép không hợp lệ (SICK, CASUAL, VACATION)',
  })
  type?: LeaveType;

  @IsOptional()
  @IsString()
  reason?: string;
}
