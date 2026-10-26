import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Artesania } from '../../core/models/artesania.model';

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
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.cargarProductos();
  }

  cargarProductos(): void {
    this.cargando = true;
    this.http.get<Artesania[]>(`${this.baseUrl}/productos`).subscribe({
      next: (data) => {
        this.artesanias = data;
        this.extraerTalleresUnicos(data);
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

  aplicarFiltros(): void {
    let resultado = [...this.artesanias];

    // 1. Filtrar por Taller
    if (this.tallerSeleccionado !== 'todos') {
      const idTaller = Number(this.tallerSeleccionado);
      resultado = resultado.filter((item: any) => (item.taller_id || item.artesano_id) === idTaller);
    }

    // 2. Filtrar por Calidad
    if (this.calidadSeleccionada !== 'todas') {
      resultado = resultado.filter((item: any) => {
        const calidadItem = item.calidad || item.calidad_partidas || '';
        return calidadItem.toLowerCase() === this.calidadSeleccionada.toLowerCase();
      });
    }

    // 3. Ordenar por Precio
    if (this.ordenPrecio === 'menor_mayor') {
      resultado.sort((a: any, b: any) => (a.precio || a.precio_promedio || 0) - (b.precio || b.precio_promedio || 0));
    } else if (this.ordenPrecio === 'mayor_menor') {
      resultado.sort((a: any, b: any) => (b.precio || b.precio_promedio || 0) - (a.precio || a.precio_promedio || 0));
    }

    // 4. Ordenar por Fecha
    if (this.ordenFecha === 'antiguos') {
      resultado.sort((a: any, b: any) => (a.id || 0) - (b.id || 0));
    } else {
      resultado.sort((a: any, b: any) => (b.id || 0) - (a.id || 0));
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