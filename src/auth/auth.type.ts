import { LoginReqBodyDto, RegisterReqBodyDto } from './auth.dto.js';

export type RegisterReqBodyType = InstanceType<typeof RegisterReqBodyDto>;
export type CreateEmployeeBodyType = Omit<RegisterReqBodyType, 'confirmPassword'>;
export type LoginReqBodyType = InstanceType<typeof LoginReqBodyDto>;
