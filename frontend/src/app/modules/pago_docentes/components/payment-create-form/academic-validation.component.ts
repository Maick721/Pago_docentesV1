import { Component, input } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import type { PaymentCreateForm } from '../../models/payment-form';
import type { RequirementStatus } from '../../models/payment.models';

@Component({
  selector: 'app-academic-validation',
  imports: [ReactiveFormsModule, MatFormFieldModule, MatSelectModule],
  templateUrl: './academic-validation.component.html',
  styleUrl: './payment-create-sections.scss',
})
export class AcademicValidationComponent {
  readonly form = input.required<PaymentCreateForm>();
  readonly requirementOptions: { value: RequirementStatus; label: string }[] = [
    { value: 'CUMPLE', label: 'Cumple' },
    { value: 'NO_CUMPLE', label: 'No cumple' },
    { value: 'PENDIENTE', label: 'Pendiente' },
  ];
}
