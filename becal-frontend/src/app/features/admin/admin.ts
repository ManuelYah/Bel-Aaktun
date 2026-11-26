import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import {
  AdminService,
  EstadoMensaje,
  EstadoResena,
  FiltroMensaje,
  FiltroResena,
  MensajeContacto,
  ProductoCatalogo,
  ResenaAdmin,
  ResumenAdmin
} from '../../core/services/admin.service';
import { AuthService } from '../../core/services/auth';

type Pestana = 'resenas' | 'mensajes' | 'productos';

@Component({
  selector: 'app-admin',
  standalone: true,
  templateUrl: './admin.html',
  styleUrl: './admin.css'
})
export class Admin implements OnInit {
  private api = inject(AdminService);
  private auth = inject(AuthService);

  usuario = this.auth.currentUser;

  pestana = signal<Pestana>('resenas');
  filtroResenas = signal<FiltroResena>('PENDIENTE');
  filtroMensajes = signal<FiltroMensaje>('NUEVO');

  resenas = signal<ResenaAdmin[]>([]);
  mensajes = signal<MensajeContacto[]>([]);
  productos = signal<ProductoCatalogo[]>([]);
  confirmandoId = signal<string | null>(null);
  resumen = signal<ResumenAdmin>({ comentarios_pendientes: 0, mensajes_nuevos: 0 });

  cargando = signal(false);
  error = signal('');
  aviso = signal('');
  trabajandoId = signal<number | null>(null);

  rechazandoId = signal<number | null>(null);
  motivo = signal('');
  fotoAmpliada = signal<string | null>(null);

  readonly filtrosResenas: { valor: FiltroResena; etiqueta: string }[] = [
    { valor: 'PENDIENTE', etiqueta: 'Pendientes' },
    { valor: 'APROBADO', etiqueta: 'Aprobadas' },
    { valor: 'RECHAZADO', etiqueta: 'Rechazadas' },
    { valor: 'TODOS', etiqueta: 'Todas' }
  ];
  readonly filtrosMensajes: { valor: FiltroMensaje; etiqueta: string }[] = [
    { valor: 'NUEVO', etiqueta: 'Nuevos' },
    { valor: 'LEIDO', etiqueta: 'Leídos' },
    { valor: 'ARCHIVADO', etiqueta: 'Archivados' },
    { valor: 'TODOS', etiqueta: 'Todos' }
  ];

  textoVacioResenas = computed(() => {
    switch (this.filtroResenas()) {
      case 'PENDIENTE':
        return 'No hay reseñas por revisar. Cuando un visitante publique una, aparecerá aquí.';
      case 'APROBADO':
        return 'Todavía no has aprobado reseñas.';
      case 'RECHAZADO':
        return 'No has rechazado ninguna reseña.';
      default:
        return 'Aún no hay reseñas.';
    }
  });

  ngOnInit(): void {
    this.recargarTodo();
  }

  // ---------------------------------------------------------------- carga
  recargarTodo(): void {
    this.cargarResumen();
    this.cargarResenas();
    this.cargarMensajes();
    this.cargarProductos();
  }

  cargarProductos(): void {
    this.api.productos().subscribe({
      next: (lista) => this.productos.set(lista),
      error: (e) => this.manejarError(e)
    });
  }

  pedirConfirmacion(clave: string): void {
    this.confirmandoId.set(clave);
  }

  cancelarConfirmacion(): void {
    this.confirmandoId.set(null);
  }

  eliminarProducto(producto: ProductoCatalogo): void {
    this.trabajandoId.set(producto.id);
    this.api.eliminarProducto(producto.id).subscribe({
      next: () => {
        this.trabajandoId.set(null);
        this.confirmandoId.set(null);
        this.mostrarAviso('Producto eliminado del catálogo.');
        this.cargarProductos();
      },
      error: (e) => {
        this.trabajandoId.set(null);
        this.confirmandoId.set(null);
        this.manejarError(e);
      }
    });
  }

  cargarResumen(): void {
    this.api.resumen().subscribe({
      next: (r) => this.resumen.set(r),
      error: (e) => this.manejarError(e)
    });
  }

  cargarResenas(): void {
    this.cargando.set(true);
    this.api.resenas(this.filtroResenas()).subscribe({
      next: (lista) => {
        this.resenas.set(lista);
        this.cargando.set(false);
        this.error.set('');
      },
      error: (e) => {
        this.cargando.set(false);
        this.manejarError(e);
      }
    });
  }

  cargarMensajes(): void {
    this.api.mensajes(this.filtroMensajes()).subscribe({
      next: (lista) => this.mensajes.set(lista),
      error: (e) => this.manejarError(e)
    });
  }

  cambiarFiltroResenas(valor: FiltroResena): void {
    this.filtroResenas.set(valor);
    this.rechazandoId.set(null);
    this.cargarResenas();
  }

  cambiarFiltroMensajes(valor: FiltroMensaje): void {
    this.filtroMensajes.set(valor);
    this.cargarMensajes();
  }

  // ---------------------------------------------------------------- reseñas
  aprobar(resena: ResenaAdmin): void {
    this.moderar(resena, 'APROBADO', 'Reseña aprobada: ya aparece en el foro.');
  }

  abrirRechazo(resena: ResenaAdmin): void {
    this.motivo.set('');
    this.rechazandoId.set(resena.id);
  }

  cancelarRechazo(): void {
    this.rechazandoId.set(null);
  }

  escribirMotivo(evento: Event): void {
    this.motivo.set((evento.target as HTMLTextAreaElement).value);
  }

  confirmarRechazo(resena: ResenaAdmin): void {
    this.moderar(resena, 'RECHAZADO', 'Reseña rechazada: no se mostrará en el foro.', this.motivo());
  }

  regresarAPendiente(resena: ResenaAdmin): void {
    this.moderar(resena, 'PENDIENTE', 'La reseña volvió a pendientes.');
  }

  private moderar(resena: ResenaAdmin, estado: EstadoResena, mensaje: string, motivo = ''): void {
    this.trabajandoId.set(resena.id);
    this.api.moderarResena(resena.id, estado, motivo).subscribe({
      next: () => {
        this.trabajandoId.set(null);
        this.rechazandoId.set(null);
        this.mostrarAviso(mensaje);
        this.cargarResenas();
        this.cargarResumen();
      },
      error: (e) => {
        this.trabajandoId.set(null);
        this.manejarError(e);
      }
    });
  }

  eliminarResena(resena: ResenaAdmin): void {
    this.trabajandoId.set(resena.id);
    this.api.eliminarResena(resena.id).subscribe({
      next: () => {
        this.trabajandoId.set(null);
        this.confirmandoId.set(null);
        this.mostrarAviso('Reseña eliminada.');
        this.cargarResenas();
        this.cargarResumen();
      },
      error: (e) => {
        this.trabajandoId.set(null);
        this.manejarError(e);
      }
    });
  }

  estrellas(valor: number): string {
    const n = Math.max(0, Math.min(5, Math.round(valor)));
    return '★'.repeat(n) + '☆'.repeat(5 - n);
  }

  etiquetaEstado(estado: EstadoResena): string {
    return { PENDIENTE: 'Pendiente', APROBADO: 'Aprobada', RECHAZADO: 'Rechazada' }[estado];
  }

  ampliarFoto(url: string): void {
    this.fotoAmpliada.set(url);
  }

  cerrarFoto(): void {
    this.fotoAmpliada.set(null);
  }

  // ---------------------------------------------------------------- mensajes
  marcarMensaje(mensaje: MensajeContacto, estado: EstadoMensaje, aviso: string): void {
    this.trabajandoId.set(mensaje.id);
    this.api.actualizarMensaje(mensaje.id, estado).subscribe({
      next: () => {
        this.trabajandoId.set(null);
        this.mostrarAviso(aviso);
        this.cargarMensajes();
        this.cargarResumen();
      },
      error: (e) => {
        this.trabajandoId.set(null);
        this.manejarError(e);
      }
    });
  }

  eliminarMensaje(mensaje: MensajeContacto): void {
    this.trabajandoId.set(mensaje.id);
    this.api.eliminarMensaje(mensaje.id).subscribe({
      next: () => {
        this.trabajandoId.set(null);
        this.confirmandoId.set(null);
        this.mostrarAviso('Mensaje eliminado.');
        this.cargarMensajes();
        this.cargarResumen();
      },
      error: (e) => {
        this.trabajandoId.set(null);
        this.manejarError(e);
      }
    });
  }

  enlaceCorreo(mensaje: MensajeContacto): string {
    const asunto = encodeURIComponent('Respuesta a tu mensaje en Bel-Aaktun');
    return `mailto:${mensaje.email}?subject=${asunto}`;
  }

  enlaceWhatsApp(mensaje: MensajeContacto): string {
    const digitos = (mensaje.telefono || '').replace(/\D/g, '');
    // Teléfonos de 10 dígitos son de México: se agrega la lada del país.
    const numero = digitos.length === 10 ? `52${digitos}` : digitos;
    return `https://wa.me/${numero}`;
  }

  // ---------------------------------------------------------------- general
  fecha(valor: string | null | undefined): string {
    if (!valor) {
      return '';
    }
    const fecha = new Date(valor);
    return isNaN(fecha.getTime())
      ? ''
      : fecha.toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' });
  }

  cerrarSesion(): void {
    this.auth.logout();
  }

  private mostrarAviso(texto: string): void {
    this.aviso.set(texto);
    setTimeout(() => this.aviso.set(''), 4000);
  }

  private manejarError(e: HttpErrorResponse): void {
    // El interceptor ya cierra la sesión si el servidor responde 401.
    if (e.status === 401) {
      return;
    }
    this.error.set(
      e.status === 0
        ? 'No se pudo conectar con el servidor. Revisa que el backend esté en marcha.'
        : e.error?.error || 'Ocurrió un error inesperado. Inténtalo de nuevo.'
    );
  }
}
