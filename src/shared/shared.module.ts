import { Global, Module } from '@nestjs/common';
import { PrismaService } from './services/prisma.service.js';
import { SharedAuthRepository } from './repositories/shared_auth.repository.js';

const sharedServices = [PrismaService, SharedAuthRepository];

@Global()
@Module({
  providers: [...sharedServices],
  exports: [...sharedServices],
})
export class SharedModule {}
