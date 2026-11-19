import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { JwtTokenService } from './jwt-token.service';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const token = inject(JwtTokenService).getToken();

  const authenticatedRequest = token?.trim()
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(authenticatedRequest);
};
