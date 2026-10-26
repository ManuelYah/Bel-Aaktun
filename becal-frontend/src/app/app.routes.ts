import { Routes } from '@angular/router';
import { Home } from './features/home/home'; //home principal
import { catalogo } from './features/catalogo/catalogo'; // Catalogo de artesanias
import { Cuevasmapa } from './features/cuevas-mapa/cuevas-mapa'; // Mapa de cuevas y talleres
import { Contacto } from './features/contacto/contacto'; // Formulario de contacto
import { CrearReserva } from './features/reserva/reserva'; // Componente para crear reservas
import { authGuard } from './core/guards/auth-guard'; // Guard para proteger rutas
import { Dashboard } from './features/dashboard/dashboard'; // Componente del dashboard
import { Login } from './features/auth/login/login'; // Componente de login

export const routes: Routes = [
  { path: '', component: Home }, // Muestra Home al entrar a localhost:4200
  { path: 'catalogo', component: catalogo }, // Muestra el catálogo de artesanías
  { path: 'cuevas-mapa', component: Cuevasmapa }, // Muestra el mapa de cuevas y talleres
  { path: 'crear-reserva', component: CrearReserva }, // Muestra el formulario para crear reservas
  { path: 'contacto', component: Contacto }, // Muestra el formulario de contacto
  { path: 'dashboard', component: Dashboard, canActivate: [authGuard] }, // Muestra el dashboard solo si el usuario está autenticado
  { path: 'login', component: Login }, // Muestra el formulario de login 
  { path: '**', redirectTo: '' }         
];