import { IsDateString, IsNotEmpty } from 'class-validator';

export class ProcessPayrollDto {
  @IsDateString({}, { message: 'pay_period_start phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'pay_period_start không được để trống' })
  pay_period_start: string;

  @IsDateString({}, { message: 'pay_period_end phải đúng định dạng YYYY-MM-DD' })
  @IsNotEmpty({ message: 'pay_period_end không được để trống' })
  pay_period_end: string;
}
