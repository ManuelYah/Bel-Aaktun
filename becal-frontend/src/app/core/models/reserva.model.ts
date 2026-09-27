export interface Reserva {
  id?: number;
  taller_id: number;
  nombre_taller?: string;
  nombre_visitante: string;
  email_visitante: string;
  telefono_visitante: string;
  numero_personas: number;
  fecha_reserva: string;
  hora_reserva: string;
  estado?: 'pendiente' | 'confirmada' | 'cancelada';
  creado_en?: string;
}

export interface SesionArtesano {
  id: number;
  nombre: string;
  email: string;
  taller_id: number;
  nombre_taller: string;
  token?: string;
}