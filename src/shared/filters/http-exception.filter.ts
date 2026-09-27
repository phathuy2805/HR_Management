import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { FailureResponse } from '../types/response.type.js';

@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const statusCode = exception.getStatus();

    const exceptionResponse = exception.getResponse();
    console.log('exceptionResponse');
    console.dir(exceptionResponse, {
      depth: null,
    });
    let message = 'Lỗi hệ thống';
    let error = exception.name;

    if (typeof exceptionResponse === 'string') {
      message = exceptionResponse;
    } else if (
      typeof exceptionResponse === 'object' &&
      exceptionResponse !== null
    ) {
      const resObj = exceptionResponse as Record<string, any>;
      console.log('resObj');
      console.dir(resObj, { depth: null });
      message = resObj.message || message;
      error = resObj.error || error;
    }

    const errorPayload: FailureResponse = {
      success: false,
      statusCode,
      message,
      error,
      timestamp: new Date().toISOString(),
    };

    response.status(statusCode).json(errorPayload);
  }
}
