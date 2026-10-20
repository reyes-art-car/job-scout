import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { PROFILE } from '../../testing/fixtures';
import { ProfileService } from '../core/profile.service';
import { AppShell } from './app-shell';

describe('AppShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppShell],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ProfileService, useValue: { profile: PROFILE, isCustom: signal(false) } },
      ],
    }).compileComponents();
  });

  it('muestra la navegación principal con las ocho secciones', () => {
    const fixture = TestBed.createComponent(AppShell);
    fixture.detectChanges();
    const links = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('nav a')).map((a) =>
      a.textContent?.trim(),
    );
    expect(links).toEqual(['Buscar ofertas', 'Panel', 'Ofertas', 'Adaptar CV', 'Carta de presentación', 'Brecha de skills', 'Mi experiencia', 'Mi historial']);
  });

  it('muestra el nombre de la candidata en el pie lateral', () => {
    const fixture = TestBed.createComponent(AppShell);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(PROFILE.name);
  });
});
