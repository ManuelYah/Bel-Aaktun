import { TestBed } from '@angular/core/testing';

import { Artesanias } from './artesanias';

describe('Artesanias', () => {
  let service: Artesanias;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Artesanias);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
