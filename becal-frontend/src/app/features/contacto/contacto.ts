import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '../../core/api.config';

@Component({
  selector: 'app-contacto',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './contacto.html',
  styleUrls: ['./contacto.css']
})
export class Contacto {
  private http = inject(HttpClient);
  private cdr = inject(ChangeDetectorRef);

  // Datos del negocio
  correo: string = 'belaaktun@gmail.com';
  whatsappNumero: string = '529969632246'; // Formato internacional (+52)

  // Modelo del formulario
  nombre: string = '';
  email: string = '';
  telefono: string = '';
  mensaje: string = '';
  /** Campo trampa: las personas no lo ven; los bots sí lo llenan. */
  website: string = '';

  enviando = false;
  exito = '';
  error = '';

  /** Guarda el mensaje para que lo vea el administrador en su panel. */
  enviarMensaje(): void {
    this.exito = '';
    this.error = '';

    if (!this.nombre.trim() || !this.mensaje.trim()) {
      this.error = 'Escribe tu nombre y tu mensaje.';
      return;
    }
    if (!this.email.trim() && !this.telefono.trim()) {
      this.error = 'Déjanos un correo o un teléfono para poder responderte.';
      return;
    }

    this.enviando = true;
    this.http
      .post<{ message: string }>(`${API_URL}/contacto`, {
        nombre: this.nombre,
        email: this.email,
        telefono: this.telefono,
        mensaje: this.mensaje,
        website: this.website
      })
      .subscribe({
        next: (res) => {
          this.enviando = false;
          this.exito = res.message || 'Mensaje recibido. Te responderemos pronto.';
          this.nombre = this.email = this.telefono = this.mensaje = '';
          this.cdr.detectChanges();
        },
        error: (err) => {
          this.enviando = false;
          this.error =
            err.status === 0
              ? 'No pudimos conectar con el servidor. Inténtalo de nuevo en unos minutos.'
              : err.error?.error || 'No pudimos enviar tu mensaje. Inténtalo de nuevo.';
          this.cdr.detectChanges();
        }
      });
  }

  enviarWhatsApp() {
    if (!this.nombre || !this.mensaje) {
      alert('Por favor completa tu nombre y mensaje.');
      return;
    }

    const texto = `Hola, mi nombre es *${this.nombre}*.\n` +
                  `Teléfono: ${this.telefono || 'No proporcionado'}\n\n` +
                  `*Consulta desde la página web Bel Áaktun:*\n${this.mensaje}`;

    const url = `https://wa.me/${this.whatsappNumero}?text=${encodeURIComponent(texto)}`;
    window.open(url, '_blank');
  }

  enviarCorreo() {
    if (!this.nombre || !this.mensaje) {
      alert('Por favor completa tu nombre y mensaje.');
      return;
    }

    const asunto = `Consulta de ${this.nombre} - Bel Áaktun`;
    const cuerpo = `Hola Bel Áaktun,\n\nMi nombre es ${this.nombre}.\nTeléfono de contacto: ${this.telefono || 'No proporcionado'}\n\nMensaje:\n${this.mensaje}`;

    const mailtoUrl = `mailto:${this.correo}?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(cuerpo)}`;
    window.location.href = mailtoUrl;
  }
}
