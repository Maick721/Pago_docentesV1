import { Component, computed, input, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { PaymentLookups } from '../../models/payment.models';

@Component({
  selector: 'app-career-filter',
  imports: [ReactiveFormsModule, MatFormFieldModule, MatInputModule],
  templateUrl: './career-filter.component.html',
})
export class CareerFilterComponent {
  readonly control = input.required<FormControl<string | null>>();
  readonly careers = input.required<PaymentLookups['carreras']>();
  readonly open = signal(false);
  readonly options = signal<PaymentLookups['carreras']>([]);
  readonly activeIndex = signal(-1);
  readonly groups = computed(() => {
    const groups = new Map<string, PaymentLookups['carreras']>();
    for (const career of this.options()) {
      const name = career.grupo?.trim() || 'Otras carreras';
      groups.set(name, [...(groups.get(name) ?? []), career]);
    }
    return [...groups.entries()].map(([name, careers]) => ({ name, careers }));
  });

  update(): void {
    const query = this.normalize(this.control().value?.trim() ?? '');
    this.options.set(this.careers()
      .filter((career) =>
        !query || this.normalize(`${career.nombre} ${career.grupo ?? ''}`).includes(query),
      )
      .slice(0, 8));
    this.activeIndex.set(-1);
    this.open.set(true);
  }

  select(career: PaymentLookups['carreras'][number]): void {
    this.control().setValue(career.nombre);
    this.close();
  }

  onKeydown(event: KeyboardEvent): void {
    const count = this.options().length;
    if (event.key === 'Escape') {
      this.close();
    } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (!this.open()) this.update();
      if (count > 0) {
        const step = event.key === 'ArrowDown' ? 1 : -1;
        this.activeIndex.update((index) => Math.max(0, Math.min(count - 1, index + step)));
      }
    } else if (event.key === 'Enter' && this.open()) {
      const career = this.options()[this.activeIndex()];
      if (career) {
        event.preventDefault();
        this.select(career);
      }
    }
  }

  activeOptionId(): string | null {
    const career = this.options()[this.activeIndex()];
    return career ? `career-filter-option-${career.id}` : null;
  }

  close(): void {
    this.open.set(false);
    this.activeIndex.set(-1);
  }

  private normalize(value: string): string {
    return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  }
}
