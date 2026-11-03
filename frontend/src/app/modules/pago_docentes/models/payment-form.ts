import { FormBuilder, ValidatorFn, Validators } from '@angular/forms';
import { PaymentModel, RequirementStatus } from './payment.models';

export function createPaymentForm(fb: FormBuilder) {
  const dateRangeValidator: ValidatorFn = (control) => {
    const start = control.get('fecha_inicio')?.value;
    const end = control.get('fecha_fin')?.value;
    return typeof start === 'string' && typeof end === 'string' && start && end && end < start
      ? { invalidDateRange: true }
      : null;
  };

  return fb.group({
    modelo: fb.control<PaymentModel>('carrera', Validators.required),
    condicion: [''],
    id_docente: fb.control<number | null>(null, Validators.required),
    modulo: ['', Validators.required],
    id_carrera: fb.control<number | null>(null, Validators.required),
    id_periodo: fb.control<number | null>(null, Validators.required),
    fecha_inicio: ['', Validators.required],
    fecha_fin: ['', Validators.required],
    contrato: [''],
    codigo_eva: [''],
    paralelo: [''],
    numero_modulo: fb.control<number | null>(null, Validators.min(0)),
    materia: [''],
    programa_grupo: [''],
    turno: [''],
    jornada: [''],
    pao: [''],
    nivel: [''],
    dias_clase: fb.control<number | null>(null, Validators.min(0)),
    aulas_virtuales: fb.control<RequirementStatus | ''>(''),
    pea: fb.control<RequirementStatus | ''>(''),
    informes_finales: fb.control<RequirementStatus | ''>(''),
    guia_recursos: fb.control<RequirementStatus | ''>(''),
    registro_notas: fb.control<RequirementStatus | ''>(''),
    portafolio_sga: fb.control<RequirementStatus | ''>(''),
    horas_proyectadas: fb.control<number | null>(null, Validators.min(0)),
    horas_reales: fb.control<number | null>(null, Validators.min(0)),
    valor_hora: fb.control<number | null>(null, Validators.min(0)),
    valor_facturar: fb.control<number | null>(null, Validators.min(0)),
    descuento_porcentaje: fb.control<number | null>(null, [Validators.min(0), Validators.max(100)]),
    descuento_aplicado: fb.control<number | null>(null, Validators.min(0)),
    retencion: fb.control<number | null>(null, Validators.min(0)),
    criterio: [''],
    criterio_tthh: [''],
    observaciones: [''],
    fecha_registro_informacion: [''],
    fecha_entrega_coordinador: [''],
    fecha_correcciones: [''],
    fecha_seguimiento: [''],
    fecha_segundo_seguimiento: [''],
    fecha_entrega_financiero: [''],
    fecha_actualizacion: [''],
    fecha_aprobacion_pago: [''],
    numero_factura: [''],
    fecha_factura: [''],
    seguimiento: [''],
  }, { validators: dateRangeValidator });
}

export type PaymentCreateForm = ReturnType<typeof createPaymentForm>;
