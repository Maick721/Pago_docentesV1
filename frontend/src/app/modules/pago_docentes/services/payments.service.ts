import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import type {
  PaymentAlert,
  PaymentDraft,
  PaymentHistory,
  PaymentLookups,
  PaymentPage,
  PaymentSettings,
  PaymentSummary,
  TeacherPayment,
  ThresholdUnit,
} from '../models/payment.models';

@Injectable({ providedIn: 'root' })
export class PaymentsService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/finance/payments';

  getPayments(filters: Record<string, string | number | null>): Observable<PaymentPage> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== null && value !== '') {
        params = params.set(key, value);
      }
    }
    return this.http.get<PaymentPage>(this.baseUrl, { params });
  }

  getSummary(): Observable<PaymentSummary> {
    return this.http.get<PaymentSummary>(`${this.baseUrl}/summary`);
  }

  getAlerts(): Observable<PaymentAlert[]> {
    return this.http.get<PaymentAlert[]>(`${this.baseUrl}/alerts`);
  }

  getSettings(): Observable<PaymentSettings> {
    return this.http.get<PaymentSettings>(`${this.baseUrl}/settings`);
  }

  saveSettings(valor: number, unidad: ThresholdUnit): Observable<PaymentSettings> {
    return this.http.put<PaymentSettings>(
      `${this.baseUrl}/settings`,
      { valor, unidad },
    );
  }

  getLookups(): Observable<PaymentLookups> {
    return this.http.get<PaymentLookups>(`${this.baseUrl}/lookups`);
  }

  createPayment(payment: PaymentDraft): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(this.baseUrl, payment);
  }

  markReady(id: number, monto: number): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(
      `${this.baseUrl}/${id}/ready`,
      { monto },
    );
  }

  recordApproval(id: number, observacion: string | null): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(
      `${this.baseUrl}/${id}/approval`,
      { observacion },
    );
  }

  markPaid(
    id: number,
    details: {
      observacion: string | null;
      numero_factura: string | null;
      numero_comprobante: string | null;
    },
  ): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(`${this.baseUrl}/${id}/paid`, details);
  }

  getHistory(id: number): Observable<PaymentHistory[]> {
    return this.http.get<PaymentHistory[]>(`${this.baseUrl}/${id}/history`);
  }

}
