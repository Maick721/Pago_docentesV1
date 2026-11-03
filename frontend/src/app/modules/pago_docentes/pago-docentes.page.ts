import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { EMPTY, Subject } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap } from 'rxjs/operators';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatToolbarModule } from '@angular/material/toolbar';

import { PaymentCreateFormComponent } from './components/payment-create-form/payment-create-form.component';
import { CareerFilterComponent } from './components/career-filter/career-filter.component';
import { PaymentActionComponent } from './components/payment-action/payment-action.component';
import { PaymentListComponent } from './components/payment-list/payment-list.component';
import { PaymentOverviewComponent } from './components/payment-overview/payment-overview.component';
import { createPaymentForm } from './models/payment-form';
import type { PaymentActionType } from './models/payment-action';
import type {
  PaymentAlert,
  PaymentHistory,
  PaymentLookups,
  PaymentSummary,
  ThresholdUnit,
  TeacherPayment,
} from './models/payment.models';
import { PaymentsService } from './services/payments.service';

@Component({
  selector: 'app-pago-docentes-page',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatToolbarModule,
    PaymentCreateFormComponent,
    CareerFilterComponent,
    PaymentActionComponent,
    PaymentListComponent,
    PaymentOverviewComponent,
  ],
  templateUrl: './pago-docentes.page.html',
  styleUrl: './pago-docentes.page.scss',
})
export class PagoDocentesPage implements OnInit {
  // El servicio concentra las llamadas HTTP y FormBuilder construye formularios
  // reactivos con validaciones que la pantalla puede mostrar al usuario.
  private readonly api = inject(PaymentsService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly paymentRequests = new Subject<void>();

  // Signals guardan el estado visible de la pantalla. Al cambiar, Angular
  // actualiza automáticamente las partes de la plantilla que los consultan.
  protected readonly loading = signal(true);
  protected readonly error = signal('');
  protected readonly notice = signal('');
  protected readonly payments = signal<TeacherPayment[]>([]);
  protected readonly lookups = signal<PaymentLookups>({
    docentes: [],
    periodos: [],
    carreras: [],
  });
  protected readonly summary = signal<PaymentSummary | null>(null);
  protected readonly alerts = signal<PaymentAlert[]>([]);
  protected readonly total = signal(0);
  protected readonly page = signal(1);
  protected readonly pageSize = 20;
  protected readonly threshold = signal(30);
  protected readonly thresholdUnit = signal<ThresholdUnit>('DIAS');
  protected readonly showCreateForm = signal(false);
  protected readonly selectedAction = signal<{
    payment: TeacherPayment;
    action: PaymentActionType;
  } | null>(null);
  protected readonly expandedHistory = signal<number | null>(null);
  protected readonly expandedDetails = signal<number | null>(null);
  protected readonly history = signal<PaymentHistory[]>([]);
  protected readonly months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];
  // Filtros de consulta; al cambiar cualquiera, ngOnInit reinicia la página
  // y vuelve a pedir los resultados que correspondan.
  protected readonly filters = this.fb.group({
    q: [''],
    periodo: [''],
    mes: [''],
    carrera: [''],
    estado: [''],
  });

  protected readonly createForm = createPaymentForm(this.fb);

  protected readonly thresholdForm = this.fb.group({
    valor: [30, [Validators.required, Validators.min(1), Validators.max(365)]],
    unidad: this.fb.control<ThresholdUnit>('DIAS', Validators.required),
  });
  protected readonly actorForm = this.fb.group({
    id_usuario: this.fb.control<number | null>(null, [Validators.required, Validators.min(1)]),
  });

  ngOnInit(): void {
    this.paymentRequests
      .pipe(
        switchMap(() =>
          this.api.getPayments(this.paymentQuery()).pipe(
            catchError(() => {
              this.error.set('No se pudo cargar la bandeja de pagos.');
              this.loading.set(false);
              return EMPTY;
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((result) => {
        this.payments.set(result.items);
        this.total.set(result.total);
        this.loading.set(false);
      });

    this.filters.valueChanges
      .pipe(
        map(() => JSON.stringify(this.filters.getRawValue())),
        debounceTime(300),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        this.page.set(1);
        this.loadPayments();
      });

    this.loadAll();
  }

  protected loadAll(): void {
    // Actualiza los tres bloques de datos que componen el panel: resumen,
    // configuración de mora y listado filtrado.
    this.loading.set(true);
    this.error.set('');
    this.api.getSummary().subscribe({
      next: (summary) => this.summary.set(summary),
      error: () => this.error.set('No se pudo cargar el resumen de pagos.'),
    });
    this.api.getAlerts().subscribe({
      next: (alerts) => this.alerts.set(alerts),
      error: () => this.error.set('No se pudieron cargar las alertas de pago.'),
    });
    this.api.getSettings().subscribe({
      next: ({ valor, unidad }) => {
        this.threshold.set(valor);
        this.thresholdUnit.set(unidad);
        this.thresholdForm.controls.valor.setValue(valor, {
          emitEvent: false,
        });
        this.thresholdForm.controls.unidad.setValue(unidad, { emitEvent: false });
      },
      error: () => this.error.set('No se pudo cargar la configuración de mora.'),
    });
    this.api.getLookups().subscribe({
      next: (lookups) => this.lookups.set(lookups),
      error: () => this.error.set('No se pudieron cargar docentes, carreras y períodos.'),
    });
    this.loadPayments();
  }

  protected loadPayments(): void {
    this.loading.set(true);
    this.paymentRequests.next();
  }

  private paymentQuery(): Record<string, string | number | null> {
    const values = this.filters.getRawValue();
    return {
      q: values.q?.trim() || null,
      periodo: values.periodo?.trim() || null,
      mes: values.mes ? Number(values.mes) : null,
      carrera: values.carrera?.trim() || null,
      estado: values.estado || null,
      page: this.page(),
      page_size: this.pageSize,
    };
  }

  protected paymentSubmissionStarted(): void {
    this.error.set('');
    this.notice.set('');
  }

  protected paymentCreated(): void {
    this.showCreateForm.set(false);
    this.notice.set('El registro del docente se creó correctamente.');
    this.loadAll();
  }

  protected beginAction(payment: TeacherPayment, action: PaymentActionType): void {
    this.selectedAction.set({ payment, action });
  }

  protected paymentActionCompleted(message: string): void {
    this.selectedAction.set(null);
    this.error.set('');
    this.notice.set(message);
    this.loadAll();
  }

  protected cancelAction(): void {
    this.selectedAction.set(null);
  }

  protected saveThreshold(): void {
    const valor = this.thresholdForm.controls.valor.value;
    const unidad = this.thresholdForm.controls.unidad.value;
    if (this.thresholdForm.invalid || valor === null || !unidad) {
      this.thresholdForm.markAllAsTouched();
      return;
    }
    const actorId = this.actorId();
    if (actorId === null) {
      this.actorForm.markAllAsTouched();
      this.error.set('Indica un usuario existente para guardar la configuración.');
      return;
    }
    this.api.saveSettings(valor, unidad, actorId).subscribe({
      next: (settings) => {
        this.threshold.set(settings.valor);
        this.thresholdUnit.set(settings.unidad);
        this.notice.set('Se actualizó el umbral de alerta por mora.');
        this.loadAll();
      },
      error: () => this.error.set('No se pudo guardar el umbral de mora.'),
    });
  }

  protected toggleHistory(payment: TeacherPayment): void {
    // Abre/cierra el historial de un pago y lo carga solo cuando se solicita.
    if (this.expandedHistory() === payment.id) {
      this.expandedHistory.set(null);
      return;
    }
    this.expandedHistory.set(payment.id);
    this.api.getHistory(payment.id).subscribe({
      next: (records) => this.history.set(records),
      error: () => this.error.set('No se pudo cargar el historial de este registro.'),
    });
  }

  protected toggleDetails(payment: TeacherPayment): void {
    // Expande o contrae los campos específicos de Carrera/Validación.
    this.expandedDetails.set(this.expandedDetails() === payment.id ? null : payment.id);
  }

  protected pageCount(): number {
    // Siempre hay al menos una página, incluso cuando la búsqueda no devuelve
    // resultados, para mantener estable la navegación de la bandeja.
    return Math.max(1, Math.ceil(this.total() / this.pageSize));
  }

  protected changePage(page: number): void {
    // Evita solicitar números de página fuera del intervalo mostrado.
    if (page < 1 || page > this.pageCount()) {
      return;
    }
    this.page.set(page);
    this.loadPayments();
  }

  protected actorId(): number | null {
    const value = this.actorForm.controls.id_usuario.value;
    return value !== null && Number.isInteger(value) && value > 0 ? value : null;
  }

}
