import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';

import { Admin } from './admin';

describe('Admin', () => {
  let component: Admin;
  let fixture: ComponentFixture<Admin>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Admin],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(Admin);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('pide reseñas pendientes, mensajes nuevos y el resumen al abrir', () => {
    const urls = http.match(() => true).map((r) => r.request.urlWithParams);
    expect(urls.some((u) => u.includes('/admin/comentarios?estado=PENDIENTE'))).toBe(true);
    expect(urls.some((u) => u.includes('/admin/mensajes?estado=NUEVO'))).toBe(true);
    expect(urls.some((u) => u.endsWith('/admin/resumen'))).toBe(true);
  });

  it('pide la lista de productos al abrir y elimina uno por la API', () => {
    http.match(() => true);
    component.eliminarProducto({ id: 7 } as any);
    const req = http.expectOne((r) => r.method === 'DELETE' && r.url.endsWith('/productos/7'));
    req.flush({});
    expect(component.confirmandoId()).toBeNull();
  });

  it('arma el enlace de WhatsApp con la lada de México', () => {
    const url = component.enlaceWhatsApp({ telefono: '996 107 2280' } as any);
    expect(url).toBe('https://wa.me/529961072280');
  });
});
