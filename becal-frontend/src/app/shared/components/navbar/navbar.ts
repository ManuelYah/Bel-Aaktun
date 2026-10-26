import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css'
})
export class Navbar {
  currentLang: string = 'ES';

  setLanguage(lang: string) {
    this.currentLang = lang;
    // Aquí conectaremos luego el LanguageService para cambiar los textos globales
    console.log('Idioma seleccionado:', lang);
  }
}