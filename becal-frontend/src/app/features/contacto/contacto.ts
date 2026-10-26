import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-contacto',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './contacto.html',
  styleUrls: ['./contacto.css']
})
export class Contacto {
  // Datos del negocio
  correo: string = 'belaaktun@gmail.com';
  whatsappNumero: string = '529969632246'; // Formato internacional (+52)

  // Modelo del formulario
  nombre: string = '';
  telefono: string = '';
  mensaje: string = '';

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