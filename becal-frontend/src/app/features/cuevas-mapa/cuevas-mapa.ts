import { Component, AfterViewInit, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { CrearReserva } from '../reserva/reserva'; // Ajusta la ruta si es necesario

interface CuevaTaller {
  id: number;
  nombre_taller: string;
  artesano_encargado: string;
  calidad_partidas: string;
  precio_promedio: number;
  telefono_whatsapp: string;
  google_maps_url: string;
  imagen_url: string;
  horario: string;
  lat: number;
  lng: number;
}

@Component({
  selector: 'app-cuevas-mapa',
  standalone: true,
  imports: [CommonModule, CrearReserva],
  templateUrl: './cuevas-mapa.html',
  styleUrl: './cuevas-mapa.css'
})
export class Cuevasmapa implements AfterViewInit {
  private map!: L.Map;

  // Variables de estado para gestionar el modal de reserva
  mostrarModalReserva: boolean = false;
  tallerSeleccionado: CuevaTaller | null = null;

  constructor(private zone: NgZone) {}

  cuevas: CuevaTaller[] = [
    {
      id: 1,
      nombre_taller: 'Artesanias Ricardo Acosta',
      artesano_encargado: 'Ricardo Acosta',
      calidad_partidas: 'Calidad 4 Partidas - Finisimo',
      precio_promedio: 1200,
      telefono_whatsapp: '529992277909',
      google_maps_url: 'https://maps.app.goo.gl/dguMn9L9PYLcLREi6',
      imagen_url: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDO0b1bEzwdZq4GCvJZTGbjHhVErj_UVu-MpehuWydKA&s=10',
      horario: '9:00 AM - 7:00 PM',
      lat: 20.430735820229135,
      lng: -90.02735604098405
    },
    {
      id: 2,
      nombre_taller: 'Artesania Antonio Acosta',
      artesano_encargado: 'Don Antonio Acosta',
      calidad_partidas: 'Calidad 3 Partidas - Fino',
      precio_promedio: 780,
      telefono_whatsapp: '529994507266',
      google_maps_url: 'https://maps.google.com/?q=Artesania+Antonio+Acosta+Becal+Campeche',
      imagen_url: 'https://lh3.googleusercontent.com/grass-cs/ACvplmPZ5YLSoNRkPKYSy2_6gt5mbhe8hHscDu4qurP9CuzvtN1Uq-8yTusPiFLjpA_DG-SRTlcSvNY7zH1HKsdNHoGC3Op0goylgYASmEXnAd6D98GUMY1NiRG0_ge2OoqqaHK7-jr6pve7QvEw=s294-w294-h220-n-k-no',
      horario: '9:00 AM - 8:00 PM',
      lat: 20.444790371142204,
      lng: -90.03168610015517
    },
    {
      id: 3,
      nombre_taller: 'La casa de los sombreros Jipijapa',
      artesano_encargado: 'Taller Familiar Jipijapa',
      calidad_partidas: 'Calidad 5 Partidas - Extra Fino',
      precio_promedio: 2400,
      telefono_whatsapp: '529991416730',
      google_maps_url: 'https://maps.google.com/?q=La+casa+de+los+sombreros+Jipijapa+Becal',
      imagen_url: 'https://lh3.googleusercontent.com/grass-cs/ACvplmNvGU0M2HRM21GIAfCqkWGlAMi90F61iRDVIKorRIilGbuLwNBkL9O02UNXiijbBGdXqnow_1lcDK_xIABGBDOPh3Zuio8TV6VTYE9SWJX9rF2pBgczTuDTIdA_x8bOXDD95zYtJA=s294-w294-h220-n-k-no',
      horario: '9:00 AM - 8:00 PM',
      lat: 20.442850126392173,
      lng: -90.02753739344516
    },
    {
      id: 4,
      nombre_taller: 'Artesanias HANS',
      artesano_encargado: 'Don Hansel Pech',
      calidad_partidas: 'Calidad 2 Partidas - Regular',
      precio_promedio: 450,
      telefono_whatsapp: '529961076625',
      google_maps_url: 'https://maps.google.com/?q=Artesanias+HANS+Becal+Campeche',
      imagen_url: 'https://lh3.googleusercontent.com/grass-cs/ACvplmO8VyxLM2AI1n1RiPgDYrv0Kaw_q_Nxta-W-6xpzA8ifssCCjYQOiUikkw7F9R6U4lViJ7jfKAYbZK9FGVAlpqyv7AEhfR5lHMetiKNcZjeIGND56_uDbXlL1xRocIeHTiJ-r9m=s220-w165-h220-n-k-no',
      horario: '8:00 AM - 9:00 PM',
      lat: 20.43420417859622,
      lng: -90.02795581803984
    },
    {
      id: 5,
      nombre_taller: 'Artesanias Britos',
      artesano_encargado: 'Familia Brito',
      calidad_partidas: 'Calidad 6 Partidas - Fino Fino',
      precio_promedio: 3800,
      telefono_whatsapp: '529991098534',
      google_maps_url: 'https://maps.app.goo.gl/TYCeuW5URi2H6Hj89',
      imagen_url: '',
      horario: '9:00 AM - 7:00 PM',
      lat: 20.442557676902858,
      lng: -90.03171913355042
    },
    {
      id: 6,
      nombre_taller: 'Artesanias De Chary',
      artesano_encargado: 'Dona Chary',
      calidad_partidas: 'Calidad 4 Partidas - Especial',
      precio_promedio: 1300,
      telefono_whatsapp: '529961022368',
      google_maps_url: 'https://maps.app.goo.gl/GW1hvdFQuPLHdw1C6',
      imagen_url: 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrkvMLM9sQ-vKhtx3QtpkAG-LXIW3qVrFISUTaB-4UlhBOlg1pe8fMI7U&s=10',
      horario: '9:00 AM - 8:00 PM',
      lat: 20.441056557269327,
      lng: -90.0199181235049
    },
    {
      id: 7,
      nombre_taller: 'Artesanias Lool Jipi',
      artesano_encargado: 'Don Alfredo',
      calidad_partidas: 'Calidad 4 Partidas - Especial',
      precio_promedio: 1600,
      telefono_whatsapp: '529961098799',
      google_maps_url: 'https://maps.app.goo.gl/oQi3WVR7CeG5QctB6',
      imagen_url: 'https://visitmexico.com/media/usercontent/68f92a916d33a-WhatsApp-Image-2025-10-22-at-12_gmxdot_50_gmxdot_15-PM_gmxdot_jpeg',
      horario: '8:00 AM - 8:00 PM',
      lat: 20.437231292560757,
      lng: -90.02712249826386
    }
  ];

  ngAfterViewInit(): void {
    this.initMap();
  }

  // Métodos de control del modal
  abrirReserva(cueva: CuevaTaller): void {
    this.tallerSeleccionado = cueva;
    this.mostrarModalReserva = true;
  }

  cerrarModal(): void {
    this.mostrarModalReserva = false;
    this.tallerSeleccionado = null;
  }

  private initMap(): void {
    const iconRetinaUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png';
    const iconUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png';
    const shadowUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png';

    const customIcon = L.icon({
      iconUrl,
      iconRetinaUrl,
      shadowUrl,
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });

    this.map = L.map('mapa-cuevas').setView([20.4395, -90.0275], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(this.map);

    this.cuevas.forEach((cueva) => {
      const popupDiv = document.createElement('div');
      popupDiv.className = 'popup-cueva';
      popupDiv.style.minWidth = '180px';
      
      popupDiv.innerHTML = `
        ${cueva.imagen_url ? `<img src="${cueva.imagen_url}" alt="${cueva.nombre_taller}" style="width: 100%; height: 90px; object-fit: cover; border-radius: 4px; margin-bottom: 6px;">` : ''}
        <h4 style="font-family: Georgia, serif; margin: 0 0 4px 0; color: #2b1a11; font-size: 1rem; font-weight: bold;">${cueva.nombre_taller}</h4>
        <p style="margin: 0 0 4px 0; color: #6e5e54; font-size: 0.8rem;"><strong>Encargado:</strong> ${cueva.artesano_encargado}</p>
        <p style="margin: 0 0 4px 0; color: #4a5568; font-size: 0.75rem;"><strong>Horario:</strong> ${cueva.horario}</p>
        <p style="margin: 0 0 8px 0; color: #bc5838; font-weight: bold; font-size: 0.95rem;">$${cueva.precio_promedio} MXN</p>
        
        <div style="display: flex; gap: 4px; flex-direction: column;">
          <button id="btn-reserva-${cueva.id}" type="button" style="width: 100%; background: #2e5339; color: white; border: none; padding: 6px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.8rem;">
            📅 Reservar Visita
          </button>
          <a href="https://wa.me/${cueva.telefono_whatsapp}" target="_blank" style="text-align: center; background: #25d366; color: white; padding: 5px 8px; border-radius: 4px; text-decoration: none; font-size: 0.75rem; font-weight: bold;">
            Contactar WhatsApp
          </a>
        </div>
      `;

      // 1. Guardamos el marcador en una variable
      const marker = L.marker([cueva.lat, cueva.lng], { icon: customIcon })
        .addTo(this.map)
        .bindPopup(popupDiv);

      // 2. Asignamos el evento al abrir el popup
      marker.on('popupopen', () => {
        const btn = document.getElementById(`btn-reserva-${cueva.id}`);
        if (btn) {
          btn.onclick = () => {
            this.zone.run(() => {
              this.abrirReserva(cueva);
            });
          };
        }
      });
    });
  }

  centrarEnCueva(lat: number, lng: number): void {
    if (this.map) {
      this.map.flyTo([lat, lng], 17, { duration: 1.5 });
    }
  }
}