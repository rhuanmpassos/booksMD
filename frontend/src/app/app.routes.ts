import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/home/home.component').then(m => m.HomeComponent)
  },
  {
    path: 'status/:jobId',
    loadComponent: () => import('./pages/status/status.component').then(m => m.StatusComponent)
  },
  {
    path: '**',
    redirectTo: ''
  }
];

