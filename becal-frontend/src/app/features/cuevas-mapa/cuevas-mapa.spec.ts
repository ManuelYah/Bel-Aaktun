import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CuevasMapa } from './cuevas-mapa';

describe('CuevasMapa', () => {
  let component: CuevasMapa;
  let fixture: ComponentFixture<CuevasMapa>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CuevasMapa],
    }).compileComponents();

    fixture = TestBed.createComponent(CuevasMapa);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
