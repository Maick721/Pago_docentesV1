import { Routes } from '@angular/router';

import { PagoDocentesPage } from './modules/pago_docentes/pago-docentes.page';

export const routes: Routes = [
  { path: '', component: PagoDocentesPage },
  { path: '**', redirectTo: '' },
];
