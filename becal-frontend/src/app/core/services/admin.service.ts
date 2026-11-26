import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '../api.config';

export type EstadoResena = 'PENDIENTE' | 'APROBADO' | 'RECHAZADO';
export type FiltroResena = EstadoResena | 'TODOS';
export type EstadoMensaje = 'NUEVO' | 'LEIDO' | 'ARCHIVADO';
export type FiltroMensaje = EstadoMensaje | 'TODOS';

export interface ResumenAdmin {
  comentarios_pendientes: number;
  mensajes_nuevos: number;
}

export interface ResenaAdmin {
  id: number;
  folio: string;
  tipo_solicitud: 'RESERVA' | 'APARTADO';
  taller_id: number;
  nombre_taller: string | null;
  autor_nombre: string;
  contacto: string;
  calificacion: number;
  titulo: string;
  descripcion: string;
  estado: EstadoResena;
  motivo_rechazo: string | null;
  created_at: string;
  fotos: string[];
}

export interface MensajeContacto {
  id: number;
  nombre: string;
  email: string | null;
  telefono: string | null;
  mensaje: string;
  estado: EstadoMensaje;
  created_at: string;
}

export interface ProductoCatalogo {
  id: number;
  nombre_pieza: string | null;
  nombre_taller: string | null;
  precio: number | string | null;
  calidad: string | null;
  imagen_url: string | null;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly base = `${API_URL}/admin`;

  constructor(private http: HttpClient) {}

  resumen(): Observable<ResumenAdmin> {
    return this.http.get<ResumenAdmin>(`${this.base}/resumen`);
  }

  resenas(estado: FiltroResena): Observable<ResenaAdmin[]> {
    return this.http.get<ResenaAdmin[]>(`${this.base}/comentarios`, {
      params: new HttpParams().set('estado', estado)
    });
  }

  moderarResena(id: number, estado: EstadoResena, motivo = ''): Observable<unknown> {
    return this.http.patch(`${this.base}/comentarios/${id}`, { estado, motivo });
  }

  eliminarResena(id: number): Observable<unknown> {
    return this.http.delete(`${this.base}/comentarios/${id}`);
  }

  mensajes(estado: FiltroMensaje): Observable<MensajeContacto[]> {
    return this.http.get<MensajeContacto[]>(`${this.base}/mensajes`, {
      params: new HttpParams().set('estado', estado)
    });
  }

  actualizarMensaje(id: number, estado: EstadoMensaje): Observable<unknown> {
    return this.http.patch(`${this.base}/mensajes/${id}`, { estado });
  }

  eliminarMensaje(id: number): Observable<unknown> {
    return this.http.delete(`${this.base}/mensajes/${id}`);
  }

  productos(): Observable<ProductoCatalogo[]> {
    return this.http.get<ProductoCatalogo[]>(`${API_URL}/productos`);
  }

  eliminarProducto(id: number): Observable<unknown> {
    return this.http.delete(`${API_URL}/productos/${id}`);
  }
}
