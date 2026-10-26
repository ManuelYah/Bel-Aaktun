import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Artesania } from '../models/artesania.model';

@Injectable({
  providedIn: 'root'
})
export class ArtesaniasService {
  private apiUrl = 'http://127.0.0.1:5000/api/productos';

  constructor(private http: HttpClient) {}

  getArtesanias(): Observable<Artesania[]> {
    return this.http.get<Artesania[]>(this.apiUrl);
  }
}