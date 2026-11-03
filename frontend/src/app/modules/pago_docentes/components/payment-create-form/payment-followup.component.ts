import { Component, input } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import type { PaymentCreateForm } from '../../models/payment-form';

@Component({
  selector: 'app-payment-followup',
  imports: [ReactiveFormsModule, MatButtonModule, MatFormFieldModule, MatInputModule],
  templateUrl: './payment-followup.component.html',
  styleUrl: './payment-create-sections.scss',
})
export class PaymentFollowupComponent {
  readonly form = input.required<PaymentCreateForm>();

  openDatePicker(input: HTMLInputElement): void {
    if (typeof input.showPicker === 'function') {
      input.showPicker();
      return;
    }
    input.focus();
  }
}
