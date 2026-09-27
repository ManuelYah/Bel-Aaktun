import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Artesania } from '../models/artesania.model';

@Injectable({
  providedIn: 'root'
})
export class ArtesaniasService {
  private apiUrl = 'http://localhost:5000/api/artesanias';

  constructor(private http: HttpClient) {}

  getArtesanias(): Observable<Artesania[]> {
    return this.http.get<Artesania[]>(this.apiUrl);
  }
}


