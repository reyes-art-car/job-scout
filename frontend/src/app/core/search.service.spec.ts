import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AccountService, parseAccount } from './account.service';
import { SearchService, parseJob } from './search.service';

describe('SearchService', () => {
  let service: SearchService;
  let accounts: AccountService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(SearchService);
    accounts = TestBed.inject(AccountService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('devuelve el token al iniciar sesión', async () => {
    const result = accounts.login('ana@example.com', 'clave-larga-123');
    const req = http.expectOne('/api/auth/login');
    expect(req.request.body).toEqual({ email: 'ana@example.com', password: 'clave-larga-123' });
    req.flush({ access_token: 'abc.def.ghi', token_type: 'bearer' });
    expect(await result).toBe('abc.def.ghi');
  });

  it('rechaza una respuesta de sesión sin token', async () => {
    const result = accounts.login('ana@example.com', 'clave-larga-123');
    http.expectOne('/api/auth/login').flush({ nada: true });
    await expectAsync(result).toBeRejected();
  });

  it('el alta no devuelve sesión: solo envía las credenciales', async () => {
    const result = accounts.register('ana@example.com', 'clave-larga-123');
    const req = http.expectOne('/api/auth/register');
    expect(req.request.body).toEqual({ email: 'ana@example.com', password: 'clave-larga-123' });
    req.flush({ message: 'Revisa tu bandeja' }, { status: 202, statusText: 'Accepted' });
    await expectAsync(result).toBeResolved();
  });

  it('envía el token del enlace al confirmar el email y al restablecer la contraseña', async () => {
    const verify = accounts.verifyEmail('tok-verificar-123');
    const v = http.expectOne('/api/auth/verify-email');
    expect(v.request.body).toEqual({ token: 'tok-verificar-123' });
    v.flush(null, { status: 204, statusText: 'No Content' });
    await verify;

    const reset = accounts.resetPassword('tok-restablecer-123', 'otra-clave-larga');
    const r = http.expectOne('/api/auth/reset-password');
    expect(r.request.body).toEqual({ token: 'tok-restablecer-123', password: 'otra-clave-larga' });
    r.flush(null, { status: 204, statusText: 'No Content' });
    await reset;
  });

  it('descargar los datos pide la exportación completa al servidor', async () => {
    const result = accounts.exportData();
    http.expectOne('/api/auth/export').flush({ account: { email: 'ana@example.com' }, offers: [] });
    expect(await result).toEqual({ account: { email: 'ana@example.com' }, offers: [] });
  });

  it('borrar la cuenta envía la contraseña de confirmación', async () => {
    const result = accounts.deleteAccount('mi-clave-larga-1');
    const req = http.expectOne('/api/auth/delete-account');
    expect(req.request.body).toEqual({ password: 'mi-clave-larga-1' });
    req.flush(null, { status: 204, statusText: 'No Content' });
    await expectAsync(result).toBeResolved();
  });

  it('cerrar sesión llama al servidor', async () => {
    const result = accounts.logout();
    http.expectOne('/api/auth/logout').flush(null, { status: 204, statusText: 'No Content' });
    await result;
  });

  it('descarta búsquedas con forma inválida', async () => {
    const result = service.jobs();
    http.expectOne('/api/searches').flush([
      { id: 1, strategy: 'general', status: 'done', offers_added: 3 },
      { id: 'x', status: 'done' },
      { id: 2, status: 'hackeada' },
      'basura',
    ]);
    const jobs = await result;
    expect(jobs.length).toBe(1);
    expect(jobs[0].offers_added).toBe(3);
  });

  it('el perfil es null mientras el usuario no lo ha guardado', async () => {
    const result = service.profile();
    http.expectOne('/api/profile').flush(null);
    expect(await result).toBeNull();
  });

  it('envía la estrategia al lanzar una búsqueda', async () => {
    const result = service.start('linkedin');
    const req = http.expectOne('/api/searches');
    expect(req.request.body).toEqual({ strategy: 'linkedin' });
    req.flush({ id: 7, strategy: 'linkedin', status: 'queued' });
    expect((await result).id).toBe(7);
  });
});

describe('parsers', () => {
  it('parseAccount normaliza el plan y el cupo', () => {
    expect(parseAccount({ email: 'a@b.es', plan: 'otro', quota: { limit: 1, used: 0, remaining: 1 } })).toEqual({
      email: 'a@b.es',
      plan: 'free',
      email_verified: false,
      quota: { limit: 1, used: 0, remaining: 1 },
    });
    expect(parseAccount({ email: 'a@b.es' })).toBeNull();
  });

  it('parseJob no admite estados desconocidos', () => {
    expect(parseJob({ id: 1, status: 'queued' })?.status).toBe('queued');
    expect(parseJob({ id: 1, status: 'x' })).toBeNull();
  });
});
