export interface SuccessResponse<T> {
  success: boolean;
  statusCode: number;
  data: T;
  timestamp: string;
}

export interface FailureResponse {
  success: boolean;
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
}
