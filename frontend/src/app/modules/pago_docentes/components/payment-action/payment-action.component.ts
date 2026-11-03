import { Component, inject, input, OnChanges, output, SimpleChanges } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import type { PaymentActionType } from '../../models/payment-action';
import type { TeacherPayment } from '../../models/payment.models';
import { PaymentsService } from '../../services/payments.service';

@Component({
  selector: 'app-payment-action',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './payment-action.component.html',
  styleUrl: './payment-action.component.scss',
})
export class PaymentActionComponent implements OnChanges {
  readonly payment = input.required<TeacherPayment>();
  readonly action = input.required<PaymentActionType>();
  readonly actorId = input<number | null>(null);
  readonly cancelled = output<void>();
  readonly completed = output<string>();
  readonly failed = output<string>();
  private readonly api = inject(PaymentsService);
  private readonly fb = inject(FormBuilder);
  readonly form = this.fb.group({
    monto: this.fb.control<number | null>(null, Validators.min(0.01)),
    observacion: [''],
    numero_factura: [''],
    numero_comprobante: [''],
  });

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['payment'] || changes['action']) {
      this.form.reset();
    }
  }

  confirm(): void {
    const payment = this.payment();
    const action = this.action();
    const actorId = this.actorId();
    const values = this.form.getRawValue();
    if (actorId === null || (action === 'ready' && (values.monto === null || values.monto <= 0))) {
      this.form.markAllAsTouched();
      if (actorId === null) this.failed.emit('Indica un usuario existente para registrar la operación.');
      return;
    }

    const optionalText = (value: string | null): string | null => value?.trim() || null;
    const request = action === 'ready'
      ? this.api.markReady(payment.id, Number(values.monto), actorId)
      : action === 'approval'
        ? this.api.recordApproval(payment.id, optionalText(values.observacion), actorId)
        : this.api.markPaid(payment.id, actorId, {
            observacion: optionalText(values.observacion),
            numero_factura: optionalText(values.numero_factura),
            numero_comprobante: optionalText(values.numero_comprobante),
          });
    const message = action === 'ready'
      ? 'El módulo quedó listo y se creó el pago pendiente.'
      : action === 'approval'
        ? 'La aprobación quedó registrada manualmente.'
        : 'El pago quedó marcado como pagado.';

    request.subscribe({
      next: () => this.completed.emit(message),
      error: (error: { error?: { detail?: string } }) =>
        this.failed.emit(error.error?.detail ?? 'No se pudo actualizar el estado del pago.'),
    });
  }
}
