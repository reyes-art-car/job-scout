import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AuthToken, authInterceptor } from './auth';

describe('authInterceptor', () => {
  let http: HttpClient;
  let controller: HttpTestingController;
  let auth: AuthToken;

  beforeEach(() => {
    sessionStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(withInterceptors([authInterceptor])), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    controller = TestBed.inject(HttpTestingController);
    auth = TestBed.inject(AuthToken);
  });

  afterEach(() => {
    controller.verify();
    sessionStorage.clear();
  });

  it('no añade cabecera si no hay token', () => {
    http.get('/api/offers').subscribe();
    expect(controller.expectOne('/api/offers').request.headers.has('Authorization')).toBeFalse();
  });

  it('añade el token solo a rutas /api/', () => {
    auth.set('  secreto  ');
    http.get('/api/offers').subscribe();
    expect(controller.expectOne('/api/offers').request.headers.get('Authorization')).toBe('Bearer secreto');
  });

  it('nunca envía el token a dominios de terceros ni a otras rutas', () => {
    auth.set('secreto');
    http.get('https://evil.example/api/offers').subscribe();
    http.get('demo/offers.json').subscribe();
    expect(controller.expectOne('https://evil.example/api/offers').request.headers.has('Authorization')).toBeFalse();
    expect(controller.expectOne('demo/offers.json').request.headers.has('Authorization')).toBeFalse();
  });

  it('guarda el token en sessionStorage y nunca en localStorage', () => {
    auth.set('secreto');
    expect(sessionStorage.getItem('jobhunter.api.token')).toBe('secreto');
    expect(localStorage.getItem('jobhunter.api.token')).toBeNull();
    auth.set('');
    expect(sessionStorage.getItem('jobhunter.api.token')).toBeNull();
    expect(auth.token()).toBeNull();
  });
});
