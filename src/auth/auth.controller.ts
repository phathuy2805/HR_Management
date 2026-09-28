import { Body, Controller, Post, Request, UseGuards } from '@nestjs/common';
import type { Request as ExpressRequest } from 'express';
import { Public } from '../shared/decorators/public.decorator.js';
import { LoginReqBodyDto, RegisterReqBodyDto } from './auth.dto.js';
import { AuthService } from './auth.service.js';
import { LocalAuthGuard } from './guards/local-auth.guard.js';

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Public()
  @Post('register')
  register(@Body() body: RegisterReqBodyDto) {
    return this.authService.register(body);
  }

  @Public()
  @UseGuards(LocalAuthGuard)
  @Post('login')
  login(@Body() _body: LoginReqBodyDto, @Request() req: ExpressRequest) {
    return this.authService.login(req.user as any);
  }
}
