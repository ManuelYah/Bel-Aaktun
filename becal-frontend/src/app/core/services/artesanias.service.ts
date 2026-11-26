import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { API_URL } from '../api.config';
import { Observable } from 'rxjs';
import { Artesania } from '../models/artesania.model';

@Injectable({
  providedIn: 'root'
})
export class ArtesaniasService {
  private apiUrl = `${API_URL}/productos`;

  constructor(private http: HttpClient) {}

  getArtesanias(): Observable<Artesania[]> {
    return this.http.get<Artesania[]>(this.apiUrl);
  }
}