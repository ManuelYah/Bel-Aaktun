import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '../../core/api.config';

@Component({
  selector: 'app-seguimiento',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './seguimiento.html',
  styleUrls: ['./seguimiento.css']
})
export class Seguimiento {
  baseUrl = API_URL;
  terminoBusqueda = '';
  folioBusqueda = '';
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

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  buscarSeguimiento(): void {
    if (!this.terminoBusqueda.trim()) {
      this.mensajeError = 'Ingresa el correo o el teléfono con el que hiciste tu reserva o apartado.';
      this.cdr.detectChanges();
      return;
    }

    this.cargando = true;
    this.mensajeError = '';
    this.datosBrutos = null;
    this.limiteVisible = 5;
    this.cdr.detectChanges();

    this.http.post(`${this.baseUrl}/seguimiento`, {
      contacto: this.terminoBusqueda,
      folio: this.folioBusqueda
    }).subscribe({
      next: (res: any) => {
        this.datosBrutos = res;
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        this.cargando = false;
        this.mensajeError = err.error?.error || 'No se encontraron registros.';
        this.cdr.detectChanges();
      }
    });
  }

  abrirDetalle(item: any): void {
    this.itemSeleccionado = item;
    this.cdr.detectChanges();
  }

  cerrarDetalle(): void {
    this.itemSeleccionado = null;
    this.cdr.detectChanges();
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
    this.cdr.detectChanges();
  }
}