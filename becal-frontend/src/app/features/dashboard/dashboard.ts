import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface Reserva {
  id: number;
  taller_id: number;
  nombre_visitante: string;
  email_visitante: string;
  telefono_visitante: string;
  numero_personas: number;
  fecha_reserva: string;
  hora_reserva: string;
  estado: string;
}

interface Apartado {
  id: number;
  producto_id: number;
  taller_id: number;
  nombre_pieza?: string;
  nombre_cliente: string;
  email_cliente: string;
  telefono_cliente: string;
  cantidad: number;
  estado: string;
  respuesta_artesano?: string;
  fecha_creacion?: string;
}

interface Producto {
  id?: number;
  artesano_id?: number;
  taller_id?: number;
  nombre_pieza: string;
  descripcion: string;
  precio: number;
  calidad: string;
  imagen_url?: string;
  imagenes: string[];
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.html',
  styleUrls: ['./dashboard.css']
})
export class Dashboard implements OnInit {
  tallerId: number = 0;
  nombreTallerSesion: string = '';

  // Navegación reactiva entre las tres secciones del dashboard
  seccionActiva: 'productos' | 'apartados' | 'reservas' = 'productos';

  // Control del sidebar en dispositivos móviles
  menuAbierto: boolean = false;

  // Contador de solicitudes de apartado pendientes
  get apartadosPendientes(): number {
    return this.apartados.filter(ap =>
      (ap.estado || '').toLowerCase() === 'pendiente'
    ).length;
  }

  // Contador de reservas pendientes
  get reservasPendientes(): number {
    return this.reservas.filter(res =>
      (res.estado || '').toLowerCase() === 'pendiente'
    ).length;
  }

  // Cambia la sección visible sin recargar la página
  cambiarSeccion(
    seccion: 'productos' | 'apartados' | 'reservas'
  ): void {
    this.seccionActiva = seccion;
    this.menuAbierto = false;
  }

  // Abre o cierra el menú lateral móvil
  alternarMenu(): void {
    this.menuAbierto = !this.menuAbierto;
  }

  // Cierra el menú lateral
  cerrarMenu(): void {
    this.menuAbierto = false;
  }
  
  reservas: Reserva[] = [];
  apartados: Apartado[] = [];
  productos: Producto[] = [];

  modoEdicion: boolean = false;
  productoEditandoId: number | null = null;

  // Modal para responder apartado
  apartadoSeleccionado: Apartado | null = null;
  mostrarModalRespuesta: boolean = false;
  accionModal: 'Confirmar' | 'Cancelar' = 'Confirmar';
  mensajeArtesano: string = '';
  medioContacto: 'whatsapp' | 'email' = 'whatsapp';

  nuevoProducto: Producto = {
    nombre_pieza: '',
    descripcion: '',
    precio: 0,
    calidad: 'Fina',
    imagen_url: '',
    imagenes: ['']
  };

  private baseUrl = 'http://localhost:5000/api';

  constructor(
    private http: HttpClient,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const usuarioSesion = localStorage.getItem('usuario');
    if (usuarioSesion) {
      try {
        const usuario = JSON.parse(usuarioSesion);
        if (usuario && usuario.taller_id) {
          this.tallerId = Number(usuario.taller_id);
          this.nombreTallerSesion = usuario.nombre_taller || usuario.nombre || 'Taller Artesanal';
        }
      } catch (e) {
        console.error('Error al leer datos de la sesión:', e);
      }
    }

    if (this.tallerId) {
      this.cargarReservas();
      this.cargarApartados();
      this.cargarProductos();
    }
  }

  cargarReservas(): void {
    this.http.get<Reserva[]>(`${this.baseUrl}/reservas/taller/${this.tallerId}`).subscribe({
      next: (data) => {
        this.reservas = [...data];
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Error cargando reservas:', err)
    });
  }

  cargarApartados(): void {
    this.http.get<Apartado[]>(`${this.baseUrl}/apartados/taller/${this.tallerId}`).subscribe({
      next: (data) => {
        this.apartados = [...data];
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Error cargando apartados:', err)
    });
  }

  cargarProductos(): void {
    this.http.get<Producto[]>(`${this.baseUrl}/productos/taller/${this.tallerId}`).subscribe({
      next: (data) => {
        this.productos = data;
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Error cargando productos:', err)
    });
  }

  // --- LÓGICA DE GESTIÓN DE APARTADOS ---

  abrirModalRespuesta(apartado: Apartado, accion: 'Confirmar' | 'Cancelar'): void {
    this.apartadoSeleccionado = apartado;
    this.accionModal = accion;
    this.mostrarModalRespuesta = true;

    if (accion === 'Confirmar') {
      this.mensajeArtesano = `¡Hola ${apartado.nombre_cliente}! Te confirmo que recibimos tu pedido de (${apartado.cantidad}) pieza(s) de "${apartado.nombre_pieza || 'Artesanía'}". Estará listo para recoger el día X. El pago se realiza directamente en el taller en efectivo o transferencia.`;
    } else {
      this.mensajeArtesano = `Hola ${apartado.nombre_cliente}, respecto a tu apartado de "${apartado.nombre_pieza || 'Artesanía'}", lamentablemente no tenemos stock disponible en este momento / está en proceso de fabricación. Te notificaremos cuando tengamos disponibles.`;
    }
    this.cdr.detectChanges();
  }

  cerrarModalRespuesta(): void {
    this.mostrarModalRespuesta = false;
    this.apartadoSeleccionado = null;
    this.mensajeArtesano = '';
  }

  enviarRespuestaYActualizar(): void {
    if (!this.apartadoSeleccionado) return;

    const nuevoEstado = this.accionModal === 'Confirmar' ? 'Confirmado' : 'Cancelado';
    const payload = {
      estado: nuevoEstado,
      respuesta_artesano: this.mensajeArtesano
    };

    // 1. Guardar estado y respuesta en backend
    this.http.patch(`${this.baseUrl}/apartados/${this.apartadoSeleccionado.id}`, payload).subscribe({
      next: () => {
        // 2. Abrir WhatsApp o Cliente de Correo
        if (this.medioContacto === 'whatsapp' && this.apartadoSeleccionado?.telefono_cliente) {
          const mensajeEncoded = encodeURIComponent(this.mensajeArtesano);
          const url = `https://wa.me/${this.apartadoSeleccionado.telefono_cliente}?text=${mensajeEncoded}`;
          window.open(url, '_blank');
        } else if (this.medioContacto === 'email' && this.apartadoSeleccionado?.email_cliente) {
          const asunto = encodeURIComponent(`Estado de tu apartado - ${this.nombreTallerSesion}`);
          const cuerpo = encodeURIComponent(this.mensajeArtesano);
          const mailtoUrl = `mailto:${this.apartadoSeleccionado.email_cliente}?subject=${asunto}&body=${cuerpo}`;
          window.location.href = mailtoUrl;
        }

        alert('Apartado marcado como ' + nuevoEstado + ' y mensaje preparado para envío.');
        this.cerrarModalRespuesta();
        this.cargarApartados();
      },
      error: (err) => console.error('Error al actualizar apartado:', err)
    });
  }

  eliminarApartado(apartadoId: number): void {
    if (confirm('¿Estás seguro de eliminar este registro de apartado?')) {
      this.http.delete(`${this.baseUrl}/apartados/${apartadoId}`).subscribe({
        next: () => this.cargarApartados(),
        error: (err) => console.error('Error eliminando apartado:', err)
      });
    }
  }

  // --- CRUD DE PRODUCTOS ---

  guardarProducto(): void {
    if (!this.nuevoProducto.nombre_pieza || !this.nuevoProducto.precio) {
      alert('Por favor completa el nombre de la pieza y el precio.');
      return;
    }

    const imgsValidas = this.nuevoProducto.imagenes?.filter(img => img && img.trim() !== '') || [];
    const payload = {
      artesano_id: this.tallerId,
      taller_id: this.tallerId,
      nombre_pieza: this.nuevoProducto.nombre_pieza,
      descripcion: this.nuevoProducto.descripcion,
      precio: this.nuevoProducto.precio,
      calidad: this.nuevoProducto.calidad,
      imagen_url: imgsValidas.length > 0 ? imgsValidas[0] : '',
      imagenes: imgsValidas
    };

    if (this.modoEdicion && this.productoEditandoId) {
      this.http.put(`${this.baseUrl}/productos/${this.productoEditandoId}`, payload).subscribe({
        next: () => {
          alert('Producto actualizado exitosamente');
          this.cancelarEdicion();
          this.cargarProductos();
        },
        error: (err) => console.error('Error actualizando producto:', err)
      });
    } else {
      this.http.post(`${this.baseUrl}/productos`, payload).subscribe({
        next: () => {
          alert('Producto agregado exitosamente');
          this.cancelarEdicion();
          this.cargarProductos();
        },
        error: (err) => console.error('Error guardando producto:', err)
      });
    }
  }

  prepararEdicion(prod: Producto): void {
    this.modoEdicion = true;
    this.productoEditandoId = prod.id || null;
    let imgs: string[] = [''];
    if (prod.imagenes && prod.imagenes.length > 0) {
      imgs = [...prod.imagenes];
    } else if (prod.imagen_url) {
      imgs = [prod.imagen_url];
    }

    this.nuevoProducto = {
      nombre_pieza: prod.nombre_pieza,
      descripcion: prod.descripcion,
      precio: prod.precio,
      calidad: prod.calidad,
      imagen_url: prod.imagen_url || '',
      imagenes: imgs
    };
    this.seccionActiva = 'productos';
    this.menuAbierto = false;
  }

  cancelarEdicion(): void {
    this.modoEdicion = false;
    this.productoEditandoId = null;
    this.nuevoProducto = {
      nombre_pieza: '',
      descripcion: '',
      precio: 0,
      calidad: 'Fina',
      imagen_url: '',
      imagenes: ['']
    };
  }

  eliminarProducto(productoId?: number): void {
    if (!productoId) return;
    if (confirm('¿Estás seguro de eliminar este producto del catálogo?')) {
      this.http.delete(`${this.baseUrl}/productos/${productoId}`).subscribe({
        next: () => this.cargarProductos(),
        error: (err) => console.error('Error eliminando producto:', err)
      });
    }
  }

  cambiarEstadoReserva(reservaId: number, estado: string): void {
    this.http.patch(`${this.baseUrl}/reservas/${reservaId}`, { estado }).subscribe({
      next: () => this.cargarReservas(),
      error: (err) => console.error('Error actualizando estado de reserva:', err)
    });
  }

  eliminarReserva(reservaId: number): void {
    if (confirm('¿Estás seguro de eliminar esta reserva?')) {
      this.http.delete(`${this.baseUrl}/reservas/${reservaId}`).subscribe({
        next: () => this.cargarReservas(),
        error: (err) => console.error('Error eliminando reserva:', err)
      });
    }
  }

  onFileSelected(event: any, index: number): void {
    const file: File = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        if (!this.nuevoProducto.imagenes) this.nuevoProducto.imagenes = [];
        this.nuevoProducto.imagenes[index] = e.target.result;
        this.cdr.detectChanges();
      };
      reader.readAsDataURL(file);
    }
  }

  agregarCampoImagen(): void {
    if (!this.nuevoProducto.imagenes) this.nuevoProducto.imagenes = [''];
    if (this.nuevoProducto.imagenes.length < 3) this.nuevoProducto.imagenes.push('');
  }

  eliminarCampoImagen(index: number): void {
    if (this.nuevoProducto.imagenes && this.nuevoProducto.imagenes.length > 1) {
      this.nuevoProducto.imagenes.splice(index, 1);
    }
  }

  trackByIndex(index: number): number {
    return index;
  }
}