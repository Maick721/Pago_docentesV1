import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export type PaymentStatus = 'borrador' | 'listo' | 'aprobado' | 'pagado' | 'anulado';
export type PaymentModel = 'carrera' | 'validacion';
export type RequirementStatus = 'CUMPLE' | 'NO_CUMPLE' | 'PENDIENTE';
export type ThresholdUnit = 'DIAS' | 'MESES';

export interface PaymentModelDetails {
  modelo: PaymentModel;
  condicion?: string | null;
  contrato?: string | null;
  codigo_eva?: string | null;
  materia?: string | null;
  programa_grupo?: string | null;
  turno?: string | null;
  jornada?: string | null;
  horas_proyectadas?: number | string | null;
  horas_reales?: number | string | null;
  valor_hora?: number | string | null;
  retencion?: number | string | null;
  criterio?: string | null;
  observaciones?: string | null;
  numero_factura?: string | null;
  fecha_factura?: string | null;
  aulas_virtuales?: RequirementStatus | null;
  fecha_seguimiento?: string | null;
  fecha_segundo_seguimiento?: string | null;
  fecha_correcciones?: string | null;
}

export interface CareerPaymentDetails extends PaymentModelDetails {
  modelo: 'carrera';
  pao?: string | null;
  nivel?: string | null;
  dias_clase?: number | null;
  pea?: RequirementStatus | null;
  informes_finales?: RequirementStatus | null;
  valor_facturar?: number | string | null;
  descuento_porcentaje?: number | string | null;
  descuento_aplicado?: number | string | null;
  criterio_tthh?: string | null;
  fecha_registro_informacion?: string | null;
  fecha_entrega_coordinador?: string | null;
  fecha_entrega_financiero?: string | null;
  seguimiento?: string | null;
}

export interface ValidationPaymentDetails extends PaymentModelDetails {
  modelo: 'validacion';
  modulo_nucleo_ciclo?: string | null;
  guia_recursos?: RequirementStatus | null;
  registro_notas?: RequirementStatus | null;
  portafolio_sga?: RequirementStatus | null;
  fecha_actualizacion?: string | null;
  fecha_aprobacion_pago?: string | null;
}

export interface TeacherPayment {
  id: number;
  docente: string;
  correo_docente: string | null;
  modulo: string;
  carrera: string;
  periodo_academico: string;
  fecha_inicio: string;
  fecha_fin: string;
  monto: number | string | null;
  modelo: PaymentModel;
  datos_modelo: CareerPaymentDetails | ValidationPaymentDetails | null;
  estado: PaymentStatus;
  aprobado_en: string | null;
  aprobado_por: string | null;
  pagado_en: string | null;
  dias_desde_aprobacion: number | null;
  en_mora: boolean;
  dias_desde_listo: number | null;
  listo_atrasado: boolean;
  numero_factura: string | null;
  numero_comprobante: string | null;
}

export interface PaymentDraft {
  id_docente: number;
  id_periodo: number;
  id_carrera: number;
  nombre_modulo: string;
  paralelo: string | null;
  numero_modulo: number | null;
  codigo_eva: string | null;
  fecha_inicio: string;
  fecha_fin: string;
  modelo: PaymentModel;
  contrato: string | null;
  datos_modelo: CareerPaymentDetails | ValidationPaymentDetails;
}

export interface PaymentLookups {
  docentes: { id_docente: number; nombre: string; cedula: string | null; correo: string | null }[];
  periodos: { id: number; nombre: string }[];
  carreras: { id: number; nombre: string }[];
}

export interface PaymentAlert {
  id_modulo: number;
  docente: { id_docente: number | null; nombre: string; cedula: string | null; correo: string | null };
  nombre_modulo: string;
  carrera: string;
  periodo: string;
  tipo: 'PAGO_ATRASADO';
  estado: 'ACTIVA' | 'RESUELTA';
  fecha_referencia: string;
  dias_transcurridos: number;
  umbral: number;
  unidad: ThresholdUnit;
}

export interface PaymentPage {
  items: TeacherPayment[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaymentSummary {
  total: number;
  borradores: number;
  listos: number;
  por_pagar: number;
  pagados: number;
  en_mora: number;
  listos_atrasados: number;
  monto_pendiente: number | string;
  monto_pagado: number | string;
}

export interface PaymentSettings {
  valor: number;
  unidad: ThresholdUnit;
  correo_notificacion: string | null;
}

export interface PaymentHistory {
  id: number;
  evento: string;
  detalle: string;
  actor: string;
  creado_en: string;
}

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

  saveSettings(valor: number, unidad: ThresholdUnit, actorId: number): Observable<PaymentSettings> {
    return this.http.put<PaymentSettings>(
      `${this.baseUrl}/settings`,
      { valor, unidad },
      { params: this.actorParams(actorId) },
    );
  }

  getLookups(): Observable<PaymentLookups> {
    return this.http.get<PaymentLookups>(`${this.baseUrl}/lookups`);
  }

  createPayment(payment: PaymentDraft, actorId: number): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(this.baseUrl, payment, {
      params: this.actorParams(actorId),
    });
  }

  markReady(id: number, monto: number, actorId: number): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(
      `${this.baseUrl}/${id}/ready`,
      { monto },
      { params: this.actorParams(actorId) },
    );
  }

  recordApproval(id: number, observacion: string | null, actorId: number): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(
      `${this.baseUrl}/${id}/approval`,
      { observacion },
      { params: this.actorParams(actorId) },
    );
  }

  markPaid(
    id: number,
    actorId: number,
    details: {
      observacion: string | null;
      numero_factura: string | null;
      numero_comprobante: string | null;
    },
  ): Observable<TeacherPayment> {
    return this.http.post<TeacherPayment>(`${this.baseUrl}/${id}/paid`, details, {
      params: this.actorParams(actorId),
    });
  }

  getHistory(id: number): Observable<PaymentHistory[]> {
    return this.http.get<PaymentHistory[]>(`${this.baseUrl}/${id}/history`);
  }

  private actorParams(actorId: number): HttpParams {
    return new HttpParams().set('id_usuario', actorId);
  }
}
