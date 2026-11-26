import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ComentarioForo, ForoService } from '../../core/services/foro-talleres.service';
import { ActivatedRoute } from '@angular/router';
import { take } from 'rxjs';

interface OpcionTaller {
  id: number;
  nombre: string;
}

@Component({
  selector: 'app-foro-talleres',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './foro-talleres.html',
  styleUrls: ['./foro-talleres.css']
})
export class ForoTalleres implements OnInit {
  talleres: OpcionTaller[] = [
    { id: 1, nombre: 'Artesanias Ricardo Acosta' },
    { id: 2, nombre: 'Artesania Antonio Acosta' },
    { id: 3, nombre: 'La casa de los sombreros Jipijapa' },
    { id: 4, nombre: 'Artesanias HANS' },
    { id: 5, nombre: 'Artesanias Britos' },
    { id: 6, nombre: 'Artesanias De Chary' },
    { id: 7, nombre: 'Artesanias Lool Jipi' }
  ];

  comentarios: ComentarioForo[] = [];
  filtroTallerId: number | null = null;
  expandidoId: number | null = null;

  modo: 'crear' | 'editar' = 'crear';
  mostrarFormulario = false;

  // Campos del formulario
  folio = '';
  nombre = '';
  contacto = '';
  calificacion = 5;
  titulo = '';
  descripcion = '';
  archivosSeleccionados: File[] = [];
  previsualizaciones: string[] = [];

  cargandoLista = false;
  enviando = false;
  mensajeExito = '';
  mensajeError = '';

  constructor(
    private foroService: ForoService,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.route.queryParamMap.pipe(take(1)).subscribe((params) => {
      const idParam = params.get('tallerId');
      this.filtroTallerId = idParam ? Number(idParam) : null;
      this.cargarComentarios();
    });
  }

  cargarComentarios(): void {
    this.cargandoLista = true;
    this.mensajeError = '';
    this.cdr.detectChanges();

    this.foroService.obtenerComentarios(this.filtroTallerId).subscribe({
      next: (data) => {
        this.comentarios = Array.isArray(data) ? data : [];
        this.cargandoLista = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.comentarios = [];
        this.mensajeError = 'No fue posible cargar los comentarios del foro.';
        this.cargandoLista = false;
        this.cdr.detectChanges();
      }
    });
  }

  alternarTarjeta(id: number): void {
    this.expandidoId = this.expandidoId === id ? null : id;
    this.cdr.detectChanges();
  }

  abrirFormulario(modo: 'crear' | 'editar'): void {
    this.modo = modo;
    this.mostrarFormulario = true;
    this.mensajeExito = '';
    this.mensajeError = '';
    this.limpiarArchivos();
    this.cdr.detectChanges();
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
    this.resetCampos();
    this.cdr.detectChanges();
  }

  seleccionarCalificacion(valor: number): void {
    this.calificacion = valor;
  }

  onArchivosSeleccionados(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files) return;

    this.mensajeError = '';
    const lista = Array.from(input.files);

    if (lista.length > 3) {
      this.mensajeError = 'Solo puedes subir un máximo de 3 fotos por comentario.';
      this.archivosSeleccionados = lista.slice(0, 3);
    } else {
      this.archivosSeleccionados = lista;
    }

    this.previsualizaciones = this.archivosSeleccionados.map((file) =>
      URL.createObjectURL(file)
    );
    this.cdr.detectChanges();
  }

  quitarFoto(indice: number, inputFotos?: HTMLInputElement): void {
    if (this.previsualizaciones[indice]) {
      URL.revokeObjectURL(this.previsualizaciones[indice]);
    }
    this.archivosSeleccionados.splice(indice, 1);
    this.previsualizaciones.splice(indice, 1);

    if (this.archivosSeleccionados.length === 0 && inputFotos) {
      inputFotos.value = '';
    }
    this.cdr.detectChanges();
  }

  guardarComentario(): void {
    this.mensajeExito = '';
    this.mensajeError = '';

    if (this.archivosSeleccionados.length > 3) {
      this.mensajeError = 'El límite máximo es de 3 fotos.';
      this.cdr.detectChanges();
      return;
    }

    this.enviando = true;
    this.cdr.detectChanges();

    if (this.modo === 'crear') {
      this.foroService
        .crearComentario({
          folio: this.folio,
          nombre: this.nombre,
          contacto: this.contacto,
          calificacion: this.calificacion,
          titulo: this.titulo,
          descripcion: this.descripcion,
          fotos: this.archivosSeleccionados
        })
        .subscribe({
          next: () => {
            this.enviando = false;
            this.mensajeExito = 'Tu comentario fue publicado correctamente.';
            this.resetCampos();
            this.mostrarFormulario = false;
            this.cargarComentarios();
          },
          error: (err) => {
            this.enviando = false;
            this.mensajeError =
              err?.error?.error ||
              err?.error?.message ||
              'No se pudo publicar el comentario. Verifica tus datos y folio.';
            this.cdr.detectChanges();
          }
        });
    } else {
      this.foroService
        .editarComentario({
          folio: this.folio,
          contacto: this.contacto,
          calificacion: this.calificacion,
          titulo: this.titulo,
          descripcion: this.descripcion,
          fotos: this.archivosSeleccionados
        })
        .subscribe({
          next: () => {
            this.enviando = false;
            this.mensajeExito = 'Tu comentario fue actualizado correctamente.';
            this.resetCampos();
            this.mostrarFormulario = false;
            this.cargarComentarios();
          },
          error: (err) => {
            this.enviando = false;
            this.mensajeError =
              err?.error?.error ||
              err?.error?.message ||
              'No se pudo editar el comentario. Verifica el folio y contacto.';
            this.cdr.detectChanges();
          }
        });
    }
  }

  private limpiarArchivos(): void {
    this.previsualizaciones.forEach((url) => URL.revokeObjectURL(url));
    this.archivosSeleccionados = [];
    this.previsualizaciones = [];
  }

  private resetCampos(): void {
    this.folio = '';
    this.nombre = '';
    this.contacto = '';
    this.calificacion = 5;
    this.titulo = '';
    this.descripcion = '';
    this.limpiarArchivos();
  }
}