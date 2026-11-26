import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_URL } from '../api.config';

export interface ComentarioForo {
  id: number;
  taller_id: number;
  nombre_taller: string;
  calificacion: number;
  titulo: string;
  descripcion: string;
  fotos: string[];
  created_at?: string;
  fecha_creacion?: string;
}

export interface CrearComentarioPayload {
  folio: string;
  nombre: string;
  contacto: string;
  calificacion: number;
  titulo: string;
  descripcion: string;
  fotos: File[];
}

export interface EditarComentarioPayload {
  folio: string;
  contacto: string;
  calificacion: number;
  titulo: string;
  descripcion: string;
  fotos?: File[];
}

export interface ResumenCalificacion {
  promedio_calificacion: number;
  total_resenas: number;
}

@Injectable({
  providedIn: 'root'
})
export class ForoService {
  private readonly baseUrl = `${API_URL}/foro`;
  private readonly apiUrl = `${this.baseUrl}/comentarios`;

  constructor(private http: HttpClient) {}

  obtenerComentarios(tallerId?: number | null): Observable<ComentarioForo[]> {
    let params = new HttpParams();
    if (tallerId) {
      params = params.set('taller_id', String(tallerId));
    }
    return this.http.get<ComentarioForo[]>(this.apiUrl, { params });
  }

  crearComentario(payload: CrearComentarioPayload): Observable<any> {
    const formData = new FormData();
    formData.append('folio', payload.folio.trim());
    formData.append('nombre', payload.nombre.trim());
    formData.append('contacto', payload.contacto.trim());
    formData.append('calificacion', String(payload.calificacion));
    formData.append('titulo', payload.titulo.trim());
    formData.append('descripcion', payload.descripcion.trim());

    (payload.fotos || []).slice(0, 3).forEach((archivo) => {
      formData.append('fotos', archivo, archivo.name);
    });

    return this.http.post(this.apiUrl, formData);
  }

  editarComentario(payload: EditarComentarioPayload): Observable<any> {
    const formData = new FormData();
    formData.append('folio', payload.folio.trim());
    formData.append('contacto', payload.contacto.trim());
    formData.append('calificacion', String(payload.calificacion));
    formData.append('titulo', payload.titulo.trim());
    formData.append('descripcion', payload.descripcion.trim());

    if (payload.fotos && payload.fotos.length > 0) {
      payload.fotos.slice(0, 3).forEach((archivo) => {
        formData.append('fotos', archivo, archivo.name);
      });
    }

    return this.http.put(this.apiUrl, formData);
  }

  obtenerResumenCalificaciones(): Observable<Record<number, ResumenCalificacion>> {
    return this.http.get<Record<number, ResumenCalificacion>>(`${this.baseUrl}/resumen`);
  }
}