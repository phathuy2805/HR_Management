import { ConflictException, Injectable } from '@nestjs/common';
import { hash } from 'bcrypt';
import { SharedAuthRepository } from '../shared/repositories/shared_auth.repository.js';
import { RegisterReqBodyDto } from './auth.dto.js';
import { AuthRepository } from './auth.repository.js';

const SALT_ROUND = 10;

@Injectable()
export class AuthService {
  constructor(
    private readonly authRepo: AuthRepository,
    private readonly sharedAuthRepo: SharedAuthRepository,
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
}
