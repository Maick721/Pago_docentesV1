import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import type {
  PaymentAlert,
  PaymentSummary,
  ThresholdUnit,
} from '../../models/payment.models';

@Component({
  selector: 'app-payment-overview',
  imports: [MatCardModule],
  templateUrl: './payment-overview.component.html',
  styleUrl: './payment-overview.component.scss',
})
export class PaymentOverviewComponent {
  readonly summary = input<PaymentSummary | null>(null);
  readonly alerts = input<PaymentAlert[]>([]);
  readonly threshold = input(30);
  readonly thresholdUnit = input<ThresholdUnit>('DIAS');

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
