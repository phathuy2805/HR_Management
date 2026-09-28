import { ApiProperty } from '@nestjs/swagger';
import { IsDateString, IsNotEmpty } from 'class-validator';

export class ProcessPayrollDto {
  @ApiProperty({
    description: 'Ngày bắt đầu kỳ tính lương (YYYY-MM-DD)',
    example: '2026-09-01',
  })
  @IsDateString({}, { message: 'pay_period_start phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'pay_period_start không được để trống' })
  pay_period_start: string;

  @ApiProperty({
    description: 'Ngày kết thúc kỳ tính lương (YYYY-MM-DD, >= pay_period_start)',
    example: '2026-09-30',
  })
  @IsDateString({}, { message: 'pay_period_end phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'pay_period_end không được để trống' })
  pay_period_end: string;
}
