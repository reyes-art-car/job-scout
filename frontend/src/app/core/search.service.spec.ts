import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { SearchService, parseAccount, parseJob } from './search.service';

describe('SearchService', () => {
  let service: SearchService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    service = TestBed.inject(SearchService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('devuelve el token al iniciar sesión', async () => {
    const result = service.login('ana@example.com', 'clave-larga-123');
    const req = http.expectOne('/api/auth/login');
    expect(req.request.body).toEqual({ email: 'ana@example.com', password: 'clave-larga-123' });
    req.flush({ access_token: 'abc.def.ghi', token_type: 'bearer' });
    expect(await result).toBe('abc.def.ghi');
  });

  it('rechaza una respuesta de sesión sin token', async () => {
    const result = service.register('ana@example.com', 'clave-larga-123');
    http.expectOne('/api/auth/register').flush({ nada: true });
    await expectAsync(result).toBeRejected();
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
      quota: { limit: 1, used: 0, remaining: 1 },
    });
    expect(parseAccount({ email: 'a@b.es' })).toBeNull();
  });

  it('parseJob no admite estados desconocidos', () => {
    expect(parseJob({ id: 1, status: 'queued' })?.status).toBe('queued');
    expect(parseJob({ id: 1, status: 'x' })).toBeNull();
  });
});
