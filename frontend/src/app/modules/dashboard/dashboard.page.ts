import { Component, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatToolbarModule } from '@angular/material/toolbar';

import {
  CareerPaymentDetails,
  PaymentAlert,
  PaymentDraft,
  PaymentHistory,
  PaymentLookups,
  PaymentModel,
  PaymentStatus,
  PaymentSummary,
  PaymentsService,
  RequirementStatus,
  ThresholdUnit,
  TeacherPayment,
  ValidationPaymentDetails,
} from '../../core/payments.service';

@Component({
  selector: 'app-dashboard-page',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatToolbarModule,
  ],
  templateUrl: './dashboard.page.html',
  styleUrl: './dashboard.page.scss',
})
export class DashboardPage implements OnInit {
  // El servicio concentra las llamadas HTTP y FormBuilder construye formularios
  // reactivos con validaciones que la pantalla puede mostrar al usuario.
  private readonly api = inject(PaymentsService);
  private readonly fb = inject(FormBuilder);

  // Signals guardan el estado visible de la pantalla. Al cambiar, Angular
  // actualiza automáticamente las partes de la plantilla que los consultan.
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
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
  protected readonly actionPayment = signal<TeacherPayment | null>(null);
  protected readonly actionType = signal<'ready' | 'approval' | 'paid' | null>(null);
  protected readonly expandedHistory = signal<number | null>(null);
  protected readonly expandedDetails = signal<number | null>(null);
  protected readonly history = signal<PaymentHistory[]>([]);
  protected readonly statusLabels: Record<PaymentStatus, string> = {
    borrador: 'Borrador',
    listo: 'Listo para pago',
    aprobado: 'Por pagar',
    pagado: 'Pagado',
    anulado: 'Anulado',
  };

  // Filtros de consulta; al cambiar cualquiera, ngOnInit reinicia la página
  // y vuelve a pedir los resultados que correspondan.
  protected readonly filters = this.fb.group({
    q: [''],
    periodo: [''],
    mes: [''],
    carrera: [''],
    estado: [''],
  });

  // Un solo formulario reúne campos comunes y campos de los dos formatos.
  // El modelo elegido determina qué conjunto específico se enviará a la API.
  protected readonly createForm = this.fb.group({
    modelo: this.fb.control<PaymentModel>('carrera', Validators.required),
    condicion: [''],
    id_docente: this.fb.control<number | null>(null, Validators.required),
    modulo: ['', Validators.required],
    id_carrera: this.fb.control<number | null>(null, Validators.required),
    id_periodo: this.fb.control<number | null>(null, Validators.required),
    fecha_inicio: ['', Validators.required],
    fecha_fin: ['', Validators.required],
    contrato: [''],
    codigo_eva: [''],
    paralelo: [''],
    numero_modulo: this.fb.control<number | null>(null, Validators.min(0)),
    materia: [''],
    programa_grupo: [''],
    turno: [''],
    jornada: [''],
    pao: [''],
    nivel: [''],
    dias_clase: this.fb.control<number | null>(null, Validators.min(0)),
    aulas_virtuales: this.fb.control<RequirementStatus | ''>(''),
    pea: this.fb.control<RequirementStatus | ''>(''),
    informes_finales: this.fb.control<RequirementStatus | ''>(''),
    guia_recursos: this.fb.control<RequirementStatus | ''>(''),
    registro_notas: this.fb.control<RequirementStatus | ''>(''),
    portafolio_sga: this.fb.control<RequirementStatus | ''>(''),
    horas_proyectadas: this.fb.control<number | null>(null, Validators.min(0)),
    horas_reales: this.fb.control<number | null>(null, Validators.min(0)),
    valor_hora: this.fb.control<number | null>(null, Validators.min(0)),
    valor_facturar: this.fb.control<number | null>(null, Validators.min(0)),
    descuento_porcentaje: this.fb.control<number | null>(null, [Validators.min(0), Validators.max(100)]),
    descuento_aplicado: this.fb.control<number | null>(null, Validators.min(0)),
    retencion: this.fb.control<number | null>(null, Validators.min(0)),
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
  });

  protected readonly actionForm = this.fb.group({
    monto: this.fb.control<number | null>(null, Validators.min(0.01)),
    observacion: [''],
    numero_factura: [''],
    numero_comprobante: [''],
  });

  protected readonly thresholdForm = this.fb.group({
    valor: [30, [Validators.required, Validators.min(1), Validators.max(365)]],
    unidad: this.fb.control<ThresholdUnit>('DIAS', Validators.required),
  });
  protected readonly actorForm = this.fb.group({
    id_usuario: this.fb.control<number | null>(null, [Validators.required, Validators.min(1)]),
  });

  ngOnInit(): void {
    // Los filtros se observan como un grupo; cualquier cambio recarga la
    // bandeja desde la primera página para evitar una página fuera de rango.
    this.filters.valueChanges.subscribe(() => {
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
    // Normaliza los valores del formulario y pide una página al backend.
    // Los filtros vacíos se convierten en null para no restringir la búsqueda.
    const values = this.filters.getRawValue();
    this.loading.set(true);
    this.api
      .getPayments({
        q: values.q?.trim() || null,
        periodo: values.periodo?.trim() || null,
        mes: values.mes ? Number(values.mes) : null,
        carrera: values.carrera?.trim() || null,
        estado: values.estado || null,
        page: this.page(),
        page_size: this.pageSize,
      })
      .subscribe({
        next: (page) => {
          this.payments.set(page.items);
          this.total.set(page.total);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar la bandeja de pagos.');
          this.loading.set(false);
        },
      });
  }

  protected createPayment(): void {
    // No envía el formulario si faltan campos obligatorios o ya hay un envío
    // en curso; markAllAsTouched hace visibles los errores de validación.
    const actorId = this.actorId();
    if (this.createForm.invalid || this.saving() || actorId === null) {
      this.createForm.markAllAsTouched();
      this.actorForm.markAllAsTouched();
      if (actorId === null) {
        this.error.set('Indica un usuario existente para registrar la operación.');
      }
      return;
    }
    this.saving.set(true);
    this.error.set('');
    this.notice.set('');
    const values = this.createForm.getRawValue();
    // Convierte campos opcionales vacíos en null. Así la API recibe una forma
    // coherente y no almacena cadenas vacías para valores no informados.
    const optionalText = (value: string | null): string | null => value?.trim() || null;
    const optionalNumber = (value: number | null): number | null =>
      value === null || value === undefined || Number.isNaN(Number(value)) ? null : Number(value);
    const optionalStatus = (value: RequirementStatus | '' | null): RequirementStatus | null =>
      value || null;
    const commonDetails = {
      // Arma primero la parte compartida por ambos modelos de pago.
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
    const details: CareerPaymentDetails | ValidationPaymentDetails =
      // El discriminador modelo define los campos exclusivos del JSON enviado.
      values.modelo === 'carrera'
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
      // Persiste las referencias relacionales y conserva los datos del formulario
      // específico del modelo en la columna JSONB ampliada del esquema.
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
        // Al confirmar el servidor, se limpia el formulario y se refrescan los
        // datos para que la lista y el resumen reflejen el registro nuevo.
        this.createForm.reset();
        this.showCreateForm.set(false);
        this.notice.set('El registro del docente se creó correctamente.');
        this.saving.set(false);
        this.loadAll();
      },
      error: (error: { error?: { detail?: string } }) => {
        this.error.set(error.error?.detail ?? 'No se pudo crear el registro.');
        this.saving.set(false);
      },
    });
  }

  protected markReady(payment: TeacherPayment): void {
    this.beginAction(payment, 'ready');
  }

  protected beginAction(payment: TeacherPayment, action: 'ready' | 'approval' | 'paid'): void {
    this.actionPayment.set(payment);
    this.actionType.set(action);
    this.actionForm.reset();
  }

  protected confirmAction(): void {
    // Verifica que exista un pago y una acción seleccionada antes de enviar.
    const payment = this.actionPayment();
    const action = this.actionType();
    const values = this.actionForm.getRawValue();
    const actorId = this.actorId();
    if (
      !payment ||
      !action ||
      actorId === null ||
      (action === 'ready' && (values.monto === null || values.monto <= 0))
    ) {
      this.actionForm.markAllAsTouched();
      this.actorForm.markAllAsTouched();
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
    this.runAction(() => request, message);
    this.actionPayment.set(null);
    this.actionType.set(null);
  }

  protected cancelAction(): void {
    this.actionPayment.set(null);
    this.actionType.set(null);
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

  protected formatMoney(amount: number | string | null): string {
    // API/PostgreSQL pueden representar Decimal como cadena; Number permite
    // usar el formateador monetario del navegador para mostrar USD.
    if (amount === null) {
      return 'Sin monto';
    }
    return new Intl.NumberFormat('es-EC', {
      style: 'currency',
      currency: 'USD',
    }).format(Number(amount));
  }

  protected formatDate(value: string): string {
    // Presenta una fecha ISO recibida de la API con formato local es-EC.
    return new Intl.DateTimeFormat('es-EC', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(new Date(value));
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

  protected statusLabel(status: PaymentStatus): string {
    return this.statusLabels[status];
  }

  protected actorId(): number | null {
    const value = this.actorForm.controls.id_usuario.value;
    return value !== null && Number.isInteger(value) && value > 0 ? value : null;
  }

  private runAction(
    request: () => ReturnType<PaymentsService['markReady']>,
    message: string,
  ): void {
    // Reutiliza el manejo de éxito/error para las transiciones de estado y,
    // tras un éxito, recarga resumen y listado para reflejar el cambio.
    this.error.set('');
    this.notice.set('');
    request().subscribe({
      next: () => {
        this.notice.set(message);
        this.loadAll();
      },
      error: (error: { error?: { detail?: string } }) =>
        this.error.set(error.error?.detail ?? 'No se pudo actualizar el estado del pago.'),
    });
  }
}
