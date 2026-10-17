import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { PROFILE } from '../testing/fixtures';
import { App } from './app';
import { ProfileService } from './core/profile.service';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ProfileService, useValue: { profile: PROFILE } },
      ],
    }).compileComponents();
  });

  it('muestra la navegación principal con las cinco secciones', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const links = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('nav a')).map((a) =>
      a.textContent?.trim(),
    );
    expect(links).toEqual(['Panel', 'Ofertas', 'Adaptar CV', 'Carta de presentación', 'Brecha de skills']);
  });

  it('muestra el nombre de la candidata en el pie lateral', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(PROFILE.name);
  });
});
