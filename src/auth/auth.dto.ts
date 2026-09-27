import { IsEmail, IsNotEmpty, IsString, MinLength } from 'class-validator';
import { IsConfirmPassword } from './auth.decorator.js';

export class RegisterReqBodyDto {
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
  @MinLength(6, { message: 'Mật khẩu phải có ít nhất 6 ký tự' })
  @IsNotEmpty({ message: 'Mật khẩu không được trống' })
  password: string;

  @IsConfirmPassword('password', {
    message: 'Mật khẩu xác nhận không khớp với mật khẩu',
  })
  confirmPassword: string;
}

export class LoginReqBodyDto {
  @IsEmail({}, { message: 'Email không đúng định dạng' })
  @IsNotEmpty({ message: 'Email không được trống' })
  email: string;

  @IsString()
  @IsNotEmpty({ message: 'Mật khẩu không được trống' })
  password: string;
}
