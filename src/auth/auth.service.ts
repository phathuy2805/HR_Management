import {
  ConflictException,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Employee, EmployeeStatus } from '@prisma/client';
import { compare, hash } from 'bcrypt';
import type { StringValue } from 'ms';
import { SharedAuthRepository } from '../shared/repositories/shared_auth.repository.js';
import { RegisterReqBodyDto } from './auth.dto.js';
import { AuthRepository } from './auth.repository.js';

const SALT_ROUND = 10;

@Injectable()
export class AuthService {
  constructor(
    private readonly authRepo: AuthRepository,
    private readonly sharedAuthRepo: SharedAuthRepository,
    private readonly jwtService: JwtService,
  ) {}
  async register(body: RegisterReqBodyDto) {
    const { email, password, confirmPassword, ...userData } = body;
    const userInDb = await this.sharedAuthRepo.findByEmail(email);
    if (userInDb) throw new ConflictException('Người dùng đã tồn tại');

    const hashedPassword = await hash(password, SALT_ROUND);

    return this.authRepo.register({
      ...userData,
      email,
      password: hashedPassword,
    });
  }

  async login(user: Omit<Employee, 'password'>) {
    const payload = {
      sub: user.id,
      email: user.email,
      role: user.role,
    };

    return {
      access_token: await this.jwtService.signAsync(payload),
      refresh_token: await this.jwtService.signAsync(
        { sub: user.id },
        { expiresIn: process.env.JWT_REFRESH_TOKEN_EXPIRE as StringValue },
      ),
    };
  }

  async validateUser(
    email: string,
    pass: string,
  ): Promise<Omit<Employee, 'password'> | null> {
    const user = await this.sharedAuthRepo.findByEmail(email);

    if (!user) return null;

    if (user.status === EmployeeStatus.TERMINATED) {
      throw new UnauthorizedException('Tài khoản đã bị vô hiệu hóa');
    }

    const isMatch = await compare(pass, user.password);
    if (!isMatch) return null;

    const { password, ...userWithouPass } = user;

    return userWithouPass;
  }
}
