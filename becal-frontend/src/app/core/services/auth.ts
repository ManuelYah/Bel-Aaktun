import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { API_URL } from '../api.config';

export type Rol = 'ADMIN' | 'ARTESANO';

export interface User {
  id: number;
  nombre: string;
  email: string;
  taller_id?: number | null;
  rol?: Rol;
}

export interface AuthResponse {
  message?: string;
  token: string;
  /** Momento en que vence la sesión (segundos desde 1970). */
  expires_at: number;
  user: User;
}

const CLAVE_TOKEN = 'bel_token';
const CLAVE_USUARIO = 'bel_user';
const CLAVE_EXPIRA = 'bel_expires';
/** El dashboard del artesano lee la sesión de esta clave. */
const CLAVE_SESION_ARTESANO = 'usuario';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = API_URL;

  // Señales de Angular para un manejo reactivo del estado del usuario
  currentUser = signal<User | null>(this.getUserFromStorage());

  constructor(private http: HttpClient, private router: Router) {}

  login(credentials: { email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/login`, credentials).pipe(
      tap((response) => {
        localStorage.setItem(CLAVE_TOKEN, response.token);
        localStorage.setItem(CLAVE_EXPIRA, String(response.expires_at));
        localStorage.setItem(CLAVE_USUARIO, JSON.stringify(response.user));
        localStorage.setItem(CLAVE_SESION_ARTESANO, JSON.stringify(response.user));
        this.currentUser.set(response.user);
      })
    );
  }

  logout(): void {
    localStorage.removeItem(CLAVE_TOKEN);
    localStorage.removeItem(CLAVE_EXPIRA);
    localStorage.removeItem(CLAVE_USUARIO);
    localStorage.removeItem(CLAVE_SESION_ARTESANO);
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    if (!this.getToken()) {
      return false;
    }
    const expira = Number(localStorage.getItem(CLAVE_EXPIRA));
    return !expira || Date.now() / 1000 < expira;
  }

  isAdmin(): boolean {
    return this.currentUser()?.rol === 'ADMIN' && this.isLoggedIn();
  }

  getToken(): string | null {
    const token = localStorage.getItem(CLAVE_TOKEN);
    // Las sesiones guardadas por la versión anterior no tenían un token real.
    return token && token !== 'undefined' ? token : null;
  }

  private getUserFromStorage(): User | null {
    try {
      const user = localStorage.getItem(CLAVE_USUARIO);
      return user ? (JSON.parse(user) as User) : null;
    } catch {
      return null;
    }
  }
}
