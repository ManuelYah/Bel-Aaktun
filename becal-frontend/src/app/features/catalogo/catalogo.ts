import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Artesania } from '../../core/models/artesania.model';
import { ForoService, ResumenCalificacion } from '../../core/services/foro-talleres.service';

interface TallerFiltro {
  id: number;
  nombre: string;
}

@Component({
  selector: 'app-catalogo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './catalogo.html',
  styleUrls: ['./catalogo.css']
})
export class catalogo implements OnInit {
  artesanias: Artesania[] = [];
  filteredArtesanias: Artesania[] = [];
  talleres: TallerFiltro[] = [];
  calidadesDisponibles: string[] = [];
  resumenCalificaciones: Record<number, ResumenCalificacion> = {};
  cargando: boolean = true;

  // Filtros
  tallerSeleccionado: string = 'todos';
  calidadSeleccionada: string = 'todas';
  ordenPrecio: string = 'sin_orden';
  ordenFecha: string = 'recientes';

  // Modales
  productoSeleccionado: any = null;
  mostrarModalDetalles: boolean = false;
  mostrarModalApartado: boolean = false;

  // Formulario para apartar
  formularioApartado = {
    nombre_cliente: '',
    email_cliente: '',
    telefono_cliente: '',
    cantidad: 1
  };

  private baseUrl = 'http://localhost:5000/api';

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef,
    private foroService: ForoService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.cargarResumenCalificaciones();
    this.cargarProductos();
  }

  irAlForo(): void {
    this.router.navigate(['/foro-talleres']);
  }

  cargarResumenCalificaciones(): void {
    this.foroService.obtenerResumenCalificaciones().subscribe({
      next: (res) => {
        this.resumenCalificaciones = res || {};
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando calificaciones del foro en catálogo:', err);
      }
    });
  }

  getPromedioItem(item: any): number {
    const tallerId = Number(item?.taller_id ?? item?.artesano_id ?? 0);
    return Number(this.resumenCalificaciones[tallerId]?.promedio_calificacion ?? 0);
  }

  getTotalResenasItem(item: any): number {
    const tallerId = Number(item?.taller_id ?? item?.artesano_id ?? 0);
    return Number(this.resumenCalificaciones[tallerId]?.total_resenas ?? 0);
  }

  cargarProductos(): void {
    this.cargando = true;
    this.http.get<Artesania[]>(`${this.baseUrl}/productos`).subscribe({
      next: (data) => {
        this.artesanias = data || [];
        this.extraerTalleresUnicos(this.artesanias);
        this.extraerCalidadesUnicas(this.artesanias);
        this.aplicarFiltros();
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error cargando catálogo:', err);
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  extraerTalleresUnicos(data: Artesania[]): void {
    const mapaTalleres = new Map<number, TallerFiltro>();
    data.forEach((item: any) => {
      const tallerId = item.taller_id || item.artesano_id;
      const nombreTaller = item.nombre_taller || 'Taller Artesanal';

      if (tallerId && !mapaTalleres.has(tallerId)) {
        mapaTalleres.set(tallerId, { id: tallerId, nombre: nombreTaller });
      }
    });
    this.talleres = Array.from(mapaTalleres.values());
  }

  extraerCalidadesUnicas(data: Artesania[]): void {
    const mapaCalidades = new Map<string, string>();
    data.forEach((item: any) => {
      const calidadRaw = (item.calidad || item.calidad_partidas || '').trim();
      if (calidadRaw) {
        const clave = calidadRaw.toLowerCase();
        if (!mapaCalidades.has(clave)) {
          mapaCalidades.set(clave, calidadRaw);
        }
      }
    });
    this.calidadesDisponibles = Array.from(mapaCalidades.values());
  }

  private obtenerPrecioNumero(item: any): number {
    const raw = item?.precio ?? item?.precio_promedio ?? 0;
    const num = Number(raw);
    return Number.isNaN(num) ? 0 : num;
  }

  aplicarFiltros(): void {
    let resultado = [...this.artesanias];

    // 1. Filtrar por Taller
    if (this.tallerSeleccionado !== 'todos') {
      const idTaller = Number(this.tallerSeleccionado);
      resultado = resultado.filter((item: any) => Number(item.taller_id || item.artesano_id) === idTaller);
    }

    // 2. Filtrar por Calidad
    if (this.calidadSeleccionada !== 'todas') {
      const objetivo = this.calidadSeleccionada.trim().toLowerCase();
      resultado = resultado.filter((item: any) => {
        const calidadItem = (item.calidad || item.calidad_partidas || '').trim().toLowerCase();
        return calidadItem === objetivo;
      });
    }

    // 3. Ordenar por Precio o por Fecha (sin que se pisen entre sí)
    if (this.ordenPrecio === 'menor_mayor') {
      resultado.sort((a: any, b: any) => this.obtenerPrecioNumero(a) - this.obtenerPrecioNumero(b));
    } else if (this.ordenPrecio === 'mayor_menor') {
      resultado.sort((a: any, b: any) => this.obtenerPrecioNumero(b) - this.obtenerPrecioNumero(a));
    } else if (this.ordenFecha === 'antiguos') {
      resultado.sort((a: any, b: any) => Number(a.id || 0) - Number(b.id || 0));
    } else {
      resultado.sort((a: any, b: any) => Number(b.id || 0) - Number(a.id || 0));
    }

    this.filteredArtesanias = resultado;
    this.cdr.detectChanges();
  }

  limpiarFiltros(): void {
    this.tallerSeleccionado = 'todos';
    this.calidadSeleccionada = 'todas';
    this.ordenPrecio = 'sin_orden';
    this.ordenFecha = 'recientes';
    this.aplicarFiltros();
  }

  // --- Gestión de Modales ---
  abrirDetalles(item: any): void {
    this.productoSeleccionado = item;
    this.mostrarModalDetalles = true;
    this.cdr.detectChanges();
  }

  cerrarModales(): void {
    this.mostrarModalDetalles = false;
    this.mostrarModalApartado = false;
    this.productoSeleccionado = null;
    this.resetFormularioApartado();
    this.cdr.detectChanges();
  }

  abrirFormularioApartado(): void {
    this.mostrarModalDetalles = false;
    this.mostrarModalApartado = true;
    this.cdr.detectChanges();
  }

  resetFormularioApartado(): void {
    this.formularioApartado = {
      nombre_cliente: '',
      email_cliente: '',
      telefono_cliente: '',
      cantidad: 1
    };
  }

  confirmarApartado(): void {
    if (!this.formularioApartado.nombre_cliente || !this.formularioApartado.telefono_cliente) {
      alert('Por favor completa los campos requeridos (Nombre y Teléfono).');
      return;
    }

    const payload = {
      producto_id: this.productoSeleccionado.id,
      taller_id: this.productoSeleccionado.taller_id || this.productoSeleccionado.artesano_id,
      ...this.formularioApartado
    };

    this.http.post<any>(`${this.baseUrl}/apartados`, payload).subscribe({
      next: (response) => {
        alert(
          `¡Solicitud de apartado registrada con éxito!\n\n` +
          `Número de Folio: ${response.folio}\n\n` +
          `Hemos enviado un correo de confirmación a tu e-mail (${this.formularioApartado.email_cliente || 'registrado'}). ` +
          `Por favor espera a que el taller o artesano revise la disponibilidad de stock o tiempo de fabricación para confirmar o rechazar tu petición.`
        );
        this.cerrarModales();
      },
      error: (err) => {
        console.error('Error al apartar producto:', err);
        alert('Hubo un error al procesar la solicitud de apartado. Por favor intenta de nuevo.');
      }
    });
  }
}