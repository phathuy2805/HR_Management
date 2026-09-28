import { LoginReqBodyDto, RegisterReqBodyDto } from './auth.dto.js';

export type RegisterReqBodyType = InstanceType<typeof RegisterReqBodyDto>;
export type CreateEmployeeBodyType = Omit<
  RegisterReqBodyType,
  'confirm_password'
>;
export type LoginReqBodyType = InstanceType<typeof LoginReqBodyDto>;
