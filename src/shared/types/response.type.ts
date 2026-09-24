export interface SuccessResponse<T> {
  succes: boolean;
  statusCode: number;
  data: T;
  timestamp: string;
}

export interface FailureResponse {
  succes: boolean;
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
}
