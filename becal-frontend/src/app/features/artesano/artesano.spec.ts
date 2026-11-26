import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AdminArtesano } from './artesano';

describe('AdminArtesano', () => {
  let component: AdminArtesano;
  let fixture: ComponentFixture<AdminArtesano>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AdminArtesano],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminArtesano);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });
  
  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
