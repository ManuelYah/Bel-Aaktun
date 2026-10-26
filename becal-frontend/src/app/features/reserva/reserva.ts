import { Component, Input, Output, EventEmitter, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Reserva } from '../../core/models/reserva.model';

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
    hora_reserva: '10:00' // Valor inicial sugerido para el selector de tiempo
  };

  exito: boolean = false;

  enviarReserva(): void {
    if (!this.nuevaReserva.nombre_visitante || !this.nuevaReserva.fecha_reserva || !this.nuevaReserva.telefono_visitante) {
      alert('Por favor completa los campos obligatorios.');
      return;
    }

    // Asignamos el ID del taller seleccionado en el mapa
    this.nuevaReserva.taller_id = this.tallerId;

    this.http.post<any>('http://localhost:5000/api/reservas', this.nuevaReserva).subscribe({
      next: (response) => {
        this.exito = true;
        
        // Mostramos el folio y la notificación de éxito
        alert(`¡Reserva realizada con éxito!\n\nNúmero de Folio: ${response.folio}\n\nHemos enviado un correo de confirmación a tu bandeja. Por favor espera a que el taller confirme o rechace tu visita.`);
        
        setTimeout(() => {
          this.exito = false;
          this.cerrarModal.emit(true);
        }, 500);
      },
      error: (err) => {
        console.error('Error al guardar la reserva:', err);
        alert('Ocurrió un error al enviar tu reserva. Intenta de nuevo.');
      }
    });
  }

  cancelar(): void {
    this.cerrarModal.emit(false);
  }
}