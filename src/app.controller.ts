import { Body, Controller, Get, Post } from '@nestjs/common';
import { IsEmail, IsNotEmpty, MinLength } from 'class-validator';
import { AppService } from './app.service.js';

class TestPipeDto {
  @IsEmail()
  email: string;
  @IsNotEmpty()
  @MinLength(6)
  password: string;
}
import { Public } from './shared/decorators/public.decorator.js';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Public()
  @Get()
  getRoot(): string {
    return this.appService.getHello();
  }

  @Get('hello')
  getHello(): string {
    return this.appService.getHello();
  }

  @Post('test-pipe')
  testPipe(@Body() body: TestPipeDto) {
    return body;
  }
}
