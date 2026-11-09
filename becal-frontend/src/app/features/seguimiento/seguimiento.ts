import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-seguimiento',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './seguimiento.html',
  styleUrls: ['./seguimiento.css']
})
export class Seguimiento {
  baseUrl = 'http://127.0.0.1:5000/api';
  terminoBusqueda = '';
  cargando = false;
  datosBrutos: any = null;
  mensajeError = '';

  // Modal de Detalle
  itemSeleccionado: any = null;

  // Filtros y Paginación
  filtroTipo: 'todos' | 'reservas' | 'apartados' = 'todos';
  filtroOrden: 'reciente' | 'antiguo' = 'reciente';
  filtroTaller: string = '';
  filtroEstado: string = '';
  limiteVisible: number = 5;

  constructor(private http: HttpClient) {}

  buscarSeguimiento(): void {
    if (!this.terminoBusqueda.trim()) {
      this.mensajeError = 'Ingresa un correo, teléfono o número de folio válido.';
      return;
    }

    this.cargando = true;
    this.mensajeError = '';
    this.datosBrutos = null;
    this.limiteVisible = 5;

    this.http.post(`${this.baseUrl}/seguimiento`, { contacto: this.terminoBusqueda }).subscribe({
      next: (res: any) => {
        this.datosBrutos = res;
        this.cargando = false;
      },
      error: (err) => {
        this.cargando = false;
        this.mensajeError = err.error?.error || 'No se encontraron registros.';
      }
    });
  }

  abrirDetalle(item: any): void {
    this.itemSeleccionado = item;
  }

  cerrarDetalle(): void {
    this.itemSeleccionado = null;
  }

  get talleresDisponibles(): string[] {
    if (!this.datosBrutos) return [];
    const talleresSet = new Set<string>();
    [...(this.datosBrutos.reservas || []), ...(this.datosBrutos.apartados || [])].forEach(item => {
      if (item.nombre_taller) talleresSet.add(item.nombre_taller);
    });
    return Array.from(talleresSet);
  }

  get resultadosFiltrados() {
    if (!this.datosBrutos) return [];
    let lista: { tipoElemento: string, data: any }[] = [];

    if (this.filtroTipo === 'todos' || this.filtroTipo === 'reservas') {
      (this.datosBrutos.reservas || []).forEach((r: any) => lista.push({ tipoElemento: 'reserva', data: r }));
    }
    if (this.filtroTipo === 'todos' || this.filtroTipo === 'apartados') {
      (this.datosBrutos.apartados || []).forEach((ap: any) => lista.push({ tipoElemento: 'apartado', data: ap }));
    }
    if (this.filtroTaller) {
      lista = lista.filter(item => item.data.nombre_taller === this.filtroTaller);
    }
    if (this.filtroEstado) {
      lista = lista.filter(item => item.data.estado?.toLowerCase() === this.filtroEstado.toLowerCase());
    }

    lista.sort((a, b) => {
      const idA = a.data.id || 0;
      const idB = b.data.id || 0;
      return this.filtroOrden === 'reciente' ? idB - idA : idA - idB;
    });

    return lista;
  }

  get resultadosPaginados() {
    return this.resultadosFiltrados.slice(0, this.limiteVisible);
  }

  cargarMas(): void {
    this.limiteVisible += 5;
  }
}