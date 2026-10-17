import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { offer } from '../../testing/fixtures';
import { OfferStorage } from './gateways/offer-storage';
import { Offer } from './models';
import { OfferStore } from './offer.store';

class MemoryStorage extends OfferStorage {
  saved: Offer[] | null = null;
  read(): Offer[] | null {
    return this.saved;
  }
  write(offers: readonly Offer[]): void {
    this.saved = [...offers];
  }
  clear(): void {
    this.saved = null;
  }
}

const tick = () => new Promise<void>((resolve) => setTimeout(resolve, 0));

describe('OfferStore', () => {
  let store: OfferStore;
  let http: HttpTestingController;
  let storage: MemoryStorage;

  beforeEach(() => {
    storage = new MemoryStorage();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: OfferStorage, useValue: storage },
      ],
    });
    store = TestBed.inject(OfferStore);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  const loadWithApi = async (flush: () => void) => {
    const loading = store.load();
    flush();
    await tick();
    return loading;
  };

  const flushApi = (body: object) => () =>
    http.expectOne((r) => r.url === '/api/offers').flush(body);

  const flushDemo = async (offers: Offer[]) => {
    await tick();
    http.expectOne('demo/offers.json').flush(offers);
  };

  it('usa la API cuando responde con datos', async () => {
    await loadWithApi(flushApi({ items: [offer({ id: 7 })] }));
    expect(store.mode()).toBe('api');
    expect(store.offers().map((o) => o.id)).toEqual([7]);
  });

  it('cae a la demo si la API está vacía', async () => {
    const loading = loadWithApi(flushApi({ items: [] }));
    await flushDemo([offer({ id: 1 })]);
    await loading;
    expect(store.mode()).toBe('demo');
    expect(store.offers()).toHaveSize(1);
  });

  it('cae a la demo si la API falla y no pide token', async () => {
    const loading = loadWithApi(() =>
      http.expectOne((r) => r.url === '/api/offers').flush('error', { status: 500, statusText: 'Server Error' }),
    );
    await flushDemo([offer({ id: 1 })]);
    await loading;
    expect(store.mode()).toBe('demo');
    expect(store.authRequired()).toBeFalse();
  });

  it('pide el token cuando la API responde 401', async () => {
    const loading = loadWithApi(() =>
      http.expectOne((r) => r.url === '/api/offers').flush({ error: 'No autenticado' }, { status: 401, statusText: 'Unauthorized' }),
    );
    await flushDemo([offer({ id: 1 })]);
    await loading;
    expect(store.authRequired()).toBeTrue();
    expect(store.mode()).toBe('demo');
  });

  it('descarta datos de la API con forma inválida', async () => {
    const loading = loadWithApi(flushApi({ items: [{ id: 'x', title: 5 }, offer({ id: 2, url: 'javascript:alert(1)' })] }));
    await loading;
    expect(store.offers().map((o) => o.id)).toEqual([2]);
    expect(store.offers()[0].url).toBeNull();
  });

  describe('en modo demo', () => {
    beforeEach(async () => {
      const loading = loadWithApi(flushApi({ items: [] }));
      await flushDemo([offer({ id: 1, code: 'OF001' })]);
      await loading;
    });

    it('cambia el estado y lo persiste', async () => {
      await store.setStatus(store.offers()[0], 'Entrevista');
      expect(store.offers()[0].kanban_status).toBe('Entrevista');
      expect(storage.saved?.[0].kanban_status).toBe('Entrevista');
    });

    it('da de alta con ID secuencial y prioridad calculada', async () => {
      const draft = { ...offer(), compatibility: 90 } as Offer;
      const created = await store.add(draft);
      expect(created.code).toBe('OF002');
      expect(created.priority).toBe('Alta');
      expect(store.offers()[0].id).toBe(created.id);
    });

    it('usa lo guardado en el navegador en lugar de la semilla', async () => {
      storage.saved = [offer({ id: 99, title: 'Guardada' })];
      const loading = loadWithApi(flushApi({ items: [] }));
      await tick();
      await loading;
      expect(store.offers().map((o) => o.title)).toEqual(['Guardada']);
    });
  });
});
