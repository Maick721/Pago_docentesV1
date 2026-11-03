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
  carreras: { id: number; nombre: string; grupo: string | null }[];
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
