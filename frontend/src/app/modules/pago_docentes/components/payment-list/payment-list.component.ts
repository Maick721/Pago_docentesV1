import { Component, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import type { PaymentActionType } from '../../models/payment-action';
import type { PaymentHistory, PaymentStatus, TeacherPayment } from '../../models/payment.models';

@Component({
  selector: 'app-payment-list',
  imports: [MatButtonModule, MatProgressSpinnerModule],
  templateUrl: './payment-list.component.html',
  styleUrl: './payment-list.component.scss',
})
export class PaymentListComponent {
  readonly loading = input.required<boolean>();
  readonly payments = input.required<TeacherPayment[]>();
  readonly total = input.required<number>();
  readonly page = input.required<number>();
  readonly pageSize = input.required<number>();
  readonly expandedHistory = input<number | null>(null);
  readonly expandedDetails = input<number | null>(null);
  readonly history = input<PaymentHistory[]>([]);
  readonly actionRequested = output<{ payment: TeacherPayment; action: PaymentActionType }>();
  readonly historyToggled = output<TeacherPayment>();
  readonly detailsToggled = output<TeacherPayment>();
  readonly pageChanged = output<number>();

  private readonly statusLabels: Record<PaymentStatus, string> = {
    borrador: 'Borrador',
    listo: 'Listo para pago',
    aprobado: 'Por pagar',
    pagado: 'Pagado',
    anulado: 'Anulado',
  };

  pageCount(): number {
    return Math.max(1, Math.ceil(this.total() / this.pageSize()));
  }

  statusLabel(status: PaymentStatus): string {
    return this.statusLabels[status];
  }

  formatMoney(amount: number | string | null): string {
    if (amount === null) return 'Sin monto';
    return new Intl.NumberFormat('es-EC', { style: 'currency', currency: 'USD' }).format(Number(amount));
  }

  formatDate(value: string): string {
    return new Intl.DateTimeFormat('es-EC', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(value));
  }
}
