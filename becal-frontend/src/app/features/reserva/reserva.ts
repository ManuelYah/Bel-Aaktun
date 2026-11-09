import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Reserva, RespuestaReserva } from '../../core/models/reserva.model';

@Component({
  selector: 'app-crear-reserva',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reserva.html',
  styleUrl: './reserva.css'
})
export class CrearReserva {
  private http = inject(HttpClient);

  @Input() tallerId!: number;
  @Input() nombreTaller: string = '';
  @Output() cerrarModal = new EventEmitter<boolean>();

  nuevaReserva: Reserva = {
    taller_id: 0,
    nombre_visitante: '',
    email_visitante: '',
    telefono_visitante: '',
    numero_personas: 1,
    fecha_reserva: '',
    hora_reserva: '10:00' // Valor inicial predeterminado
  };

  

  exito: boolean = false;

  enviarReserva(): void {
    if (
      !this.nuevaReserva.nombre_visitante ||
      !this.nuevaReserva.email_visitante ||
      !this.nuevaReserva.fecha_reserva ||
      !this.nuevaReserva.telefono_visitante
    ) {
      alert('Por favor completa todos los campos obligatorios.');
      return;
    }

    // Asignamos el ID del taller seleccionado
    this.nuevaReserva.taller_id = this.tallerId;

    this.http.post<RespuestaReserva>('http://localhost:5000/api/reservas', this.nuevaReserva).subscribe({
      next: (response) => {
        this.exito = true;
        
        // Notificación con folio de la reserva
        alert(
          `¡Reserva realizada con éxito!\n\n` +
          `Número de Folio: ${response['folio']}\n\n` +
          `Hemos enviado un correo de confirmación a tu bandeja. Por favor espera a que el taller confirme o rechace tu visita.`
        );
        
        setTimeout(() => {
          this.exito = false;
          this.cerrarModal.emit(true);
        }, 500);
      },
      error: (err) => {
        console.error('Error al guardar la reserva:', err);
        alert('Ocurrió un error al enviar tu reserva. Por favor intenta de nuevo.');
      }
    });
  }

  cancelar(): void {
    this.cerrarModal.emit(false);
  }
}