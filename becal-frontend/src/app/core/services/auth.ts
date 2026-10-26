import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';

export interface User {
  id: number;
  nombre: string;
  email: string;
  taller_id?: number;
}

export interface AuthResponse {
  token: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:5000/api'; // Ajusta la URL de tu API Flask
  
  // Señales de Angular para un manejo reactivo del estado del usuario
  currentUser = signal<User | null>(this.getUserFromStorage());

  constructor(private http: HttpClient, private router: Router) {}

  login(credentials: { email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/auth/login`, credentials).pipe(
      tap((response) => {
        localStorage.setItem('bel_token', response.token);
        localStorage.setItem('bel_user', JSON.stringify(response.user));
        this.currentUser.set(response.user);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('bel_token');
    localStorage.removeItem('bel_user');
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('bel_token');
  }

  getToken(): string | null {
    return localStorage.getItem('bel_token');
  }

  private getUserFromStorage(): User | null {
    const user = localStorage.getItem('bel_user');
    return user ? JSON.parse(user) : null;
  }
}