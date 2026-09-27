import { Body, Controller, Post } from '@nestjs/common';
import { RegisterReqBodyDto } from './auth.dto.js';
import { AuthService } from './auth.service.js';

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  register(@Body() body: RegisterReqBodyDto) {
    return this.authService.register(body);
  }
}
