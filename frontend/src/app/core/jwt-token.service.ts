import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class JwtTokenService {
  private readonly tokenKey = 'itq_access_token';

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  clearToken(): void {
    localStorage.removeItem(this.tokenKey);
  }
}
