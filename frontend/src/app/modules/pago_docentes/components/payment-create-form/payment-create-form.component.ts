import { Component, computed, inject, input, output, signal } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { AcademicValidationComponent } from './academic-validation.component';
import { PaymentFollowupComponent } from './payment-followup.component';
import { PaymentValuesComponent } from './payment-values.component';
import type { PaymentCreateForm } from '../../models/payment-form';
import {
  CareerPaymentDetails,
  PaymentDraft,
  PaymentLookups,
  RequirementStatus,
  ValidationPaymentDetails,
} from '../../models/payment.models';
import { PaymentsService } from '../../services/payments.service';

@Component({
  selector: 'app-payment-create-form',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    AcademicValidationComponent,
    PaymentValuesComponent,
    PaymentFollowupComponent,
  ],
  templateUrl: './payment-create-form.component.html',
  styleUrl: './payment-create-form.component.scss',
})
export class PaymentCreateFormComponent {
  readonly form = input.required<PaymentCreateForm>();
  readonly lookups = input.required<PaymentLookups>();
  readonly actorId = input<number | null>(null);
  readonly saving = signal(false);
  readonly started = output<void>();
  readonly created = output<void>();
  readonly failed = output<string>();
  readonly cancelled = output<void>();
  private readonly api = inject(PaymentsService);

  readonly careerGroups = computed(() => {
    const groups = new Map<string, PaymentLookups['carreras']>();
    for (const career of this.lookups().carreras) {
      const group = career.grupo?.trim() || 'Otras carreras';
      groups.set(group, [...(groups.get(group) ?? []), career]);
    }
    return [...groups.entries()].map(([name, careers]) => ({ name, careers }));
  });

  createPayment(): void {
    const form = this.form();
    const actorId = this.actorId();
    if (form.invalid || this.saving() || actorId === null) {
      form.markAllAsTouched();
      if (actorId === null) {
        this.failed.emit('Indica un usuario existente para registrar la operación.');
      }
      return;
    }

    this.saving.set(true);
    this.started.emit();
    const values = form.getRawValue();
    const optionalText = (value: string | null): string | null => value?.trim() || null;
    const optionalNumber = (value: number | null): number | null =>
      value === null || Number.isNaN(Number(value)) ? null : Number(value);
    const optionalStatus = (value: RequirementStatus | '' | null): RequirementStatus | null =>
      value || null;
    const commonDetails = {
      condicion: optionalText(values.condicion),
      contrato: optionalText(values.contrato),
      codigo_eva: optionalText(values.codigo_eva),
      materia: optionalText(values.materia),
      programa_grupo: optionalText(values.programa_grupo),
      turno: optionalText(values.turno),
      jornada: optionalText(values.jornada),
      horas_proyectadas: optionalNumber(values.horas_proyectadas),
      horas_reales: optionalNumber(values.horas_reales),
      valor_hora: optionalNumber(values.valor_hora),
      retencion: optionalNumber(values.retencion),
      criterio: optionalText(values.criterio),
      observaciones: optionalText(values.observaciones),
      numero_factura: optionalText(values.numero_factura),
      fecha_factura: optionalText(values.fecha_factura),
      aulas_virtuales: optionalStatus(values.aulas_virtuales),
      fecha_seguimiento: optionalText(values.fecha_seguimiento),
      fecha_segundo_seguimiento: optionalText(values.fecha_segundo_seguimiento),
      fecha_correcciones: optionalText(values.fecha_correcciones),
    };
    const details: CareerPaymentDetails | ValidationPaymentDetails = values.modelo === 'carrera'
      ? {
          ...commonDetails,
          modelo: 'carrera',
          pao: optionalText(values.pao),
          nivel: optionalText(values.nivel),
          dias_clase: optionalNumber(values.dias_clase),
          pea: optionalStatus(values.pea),
          informes_finales: optionalStatus(values.informes_finales),
          valor_facturar: optionalNumber(values.valor_facturar),
          descuento_porcentaje: optionalNumber(values.descuento_porcentaje),
          descuento_aplicado: optionalNumber(values.descuento_aplicado),
          criterio_tthh: optionalText(values.criterio_tthh),
          fecha_registro_informacion: optionalText(values.fecha_registro_informacion),
          fecha_entrega_coordinador: optionalText(values.fecha_entrega_coordinador),
          fecha_entrega_financiero: optionalText(values.fecha_entrega_financiero),
          seguimiento: optionalText(values.seguimiento),
        }
      : {
          ...commonDetails,
          modelo: 'validacion',
          modulo_nucleo_ciclo: optionalText(values.nivel),
          guia_recursos: optionalStatus(values.guia_recursos),
          registro_notas: optionalStatus(values.registro_notas),
          portafolio_sga: optionalStatus(values.portafolio_sga),
          fecha_actualizacion: optionalText(values.fecha_actualizacion),
          fecha_aprobacion_pago: optionalText(values.fecha_aprobacion_pago),
        };
    const payment: PaymentDraft = {
      id_docente: Number(values.id_docente),
      id_periodo: Number(values.id_periodo),
      id_carrera: Number(values.id_carrera),
      nombre_modulo: values.modulo ?? '',
      paralelo: optionalText(values.paralelo),
      numero_modulo: optionalNumber(values.numero_modulo),
      codigo_eva: optionalText(values.codigo_eva),
      fecha_inicio: values.fecha_inicio ?? '',
      fecha_fin: values.fecha_fin ?? '',
      modelo: values.modelo ?? 'carrera',
      contrato: optionalText(values.contrato),
      datos_modelo: details,
    };
    this.api.createPayment(payment, actorId).subscribe({
      next: () => {
        form.reset();
        this.saving.set(false);
        this.created.emit();
      },
      error: (error: { error?: { detail?: string } }) => {
        this.failed.emit(error.error?.detail ?? 'No se pudo crear el registro.');
        this.saving.set(false);
      },
    });
  }

  openDatePicker(input: HTMLInputElement): void {
    if (typeof input.showPicker === 'function') {
      input.showPicker();
      return;
    }
    input.focus();
  }
}
