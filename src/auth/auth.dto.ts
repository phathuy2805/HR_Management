import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsNotEmpty, IsString, MinLength } from 'class-validator';
import { IsConfirmPassword } from './auth.decorator.js';

export class RegisterReqBodyDto {
  @ApiProperty({
    description: 'Họ của nhân viên',
    example: 'Nguyen',
  })
  @IsString()
  @IsNotEmpty({ message: 'Họ không được trống' })
  first_name: string;

  @ApiProperty({
    description: 'Tên của nhân viên',
    example: 'Van A',
  })
  @IsString()
  @IsNotEmpty({ message: 'Tên không được trống' })
  last_name: string;

  @ApiProperty({
    description: 'Email duy nhất trong hệ thống',
    example: 'vana@company.com',
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
  @MinLength(6, { message: 'Mật khẩu phải có ít nhất 6 ký tự' })
  @IsNotEmpty({ message: 'Mật khẩu không được trống' })
  password: string;

  @ApiProperty({
    description: 'Mật khẩu xác nhận (phải trùng với password)',
    example: 'password123',
  })
  @IsConfirmPassword('password', {
    message: 'Mật khẩu xác nhận không khớp với mật khẩu',
  })
  confirmPassword: string;
}

export class LoginReqBodyDto {
  @ApiProperty({
    description: 'Email đăng nhập',
    example: 'vana@company.com',
  })
  @IsEmail({}, { message: 'Email không đúng định dạng' })
  @IsNotEmpty({ message: 'Email không được trống' })
  email: string;

  @ApiProperty({
    description: 'Mật khẩu tài khoản',
    example: 'password123',
  })
  @IsString()
  @IsNotEmpty({ message: 'Mật khẩu không được trống' })
  password: string;
}
