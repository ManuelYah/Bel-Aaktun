import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms'; // <-- 1. Importa FormsModule
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, FormsModule], // <-- 2. Agrégalo aquí en los imports
  templateUrl: './registro.html',
  styleUrls: ['./registro.css']
})

export class Registro {
  baseUrl = 'http://127.0.0.1:5000/api';

  nuevoUsuario = {
    nombre: '',
    email: '',
    password: '',
    taller_id: null
  };

  constructor(private http: HttpClient, private router: Router) {}

  registrarNuevoUsuario(): void {
    if (!this.nuevoUsuario.nombre || !this.nuevoUsuario.email || !this.nuevoUsuario.password) {
      alert('Por favor completa todos los campos obligatorios.');
      return;
    }

    this.http.post(`${this.baseUrl}/auth/register`, this.nuevoUsuario).subscribe({
      next: (res: any) => {
        alert('¡Usuario registrado con éxito! Ahora puedes iniciar sesión.');
        this.router.navigate(['/login']); // Redirige al login de tu app
      },
      error: (err) => {
        console.error('Error en el registro:', err);
        alert(err.error?.error || 'Ocurrió un error al registrar el usuario.');
      }
    });
  }
}