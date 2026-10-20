import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { OfferStore } from '../../core/offer.store';
import { Account, SearchJob, SearchProfile, SearchService, SearchStrategy } from '../../core/search.service';

const POLL_MS = 5000;
const HTTP_PAYMENT_REQUIRED = 402;
const HTTP_CONFLICT = 409;
const HTTP_UNAUTHORIZED = 401;
const HTTP_VALIDATION = 422;
const TERMINAL = new Set(['done', 'failed']);

const STRATEGY_LABEL: Record<string, string> = {
  general: 'General (portales de España)',
  linkedin: 'LinkedIn',
  europa: 'Internacional remoto',
};
const STATUS_LABEL: Record<string, string> = {
  queued: 'En cola',
  running: 'Buscando…',
  done: 'Terminada',
  failed: 'Fallida',
};

const splitList = (value: FormDataEntryValue | null): string[] =>
  String(value ?? '')
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter(Boolean);

/** Perfil de búsqueda del usuario y lanzador de búsquedas de ofertas con seguimiento del estado. */
@Component({
  selector: 'app-search',
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './search.html',
  styleUrl: './search.scss',
})
export class Search implements OnInit {
  private readonly api = inject(SearchService);
  private readonly store = inject(OfferStore);
  private readonly destroyRef = inject(DestroyRef);
  private timer: ReturnType<typeof setTimeout> | undefined;
  private destroyed = false;

  protected readonly loading = signal(true);
  /** Sin API o sin sesión no hay cuenta: se muestra el aviso en lugar del formulario. */
  protected readonly available = signal(false);
  protected readonly account = signal<Account | null>(null);
  protected readonly profile = signal<SearchProfile | null>(null);
  protected readonly jobs = signal<SearchJob[]>([]);
  protected readonly message = signal('');
  protected readonly error = signal('');
  protected readonly saving = signal(false);
  protected readonly starting = signal(false);

  protected readonly strategyLabel = (key: string): string => STRATEGY_LABEL[key] ?? key;
  protected readonly statusLabel = (key: string): string => STATUS_LABEL[key] ?? key;

  constructor() {
    this.destroyRef.onDestroy(() => {
      this.destroyed = true;
      clearTimeout(this.timer);
    });
  }

  async ngOnInit(): Promise<void> {
    try {
      const [account, profile, jobs] = await Promise.all([this.api.account(), this.api.profile(), this.api.jobs()]);
      this.account.set(account);
      this.profile.set(profile);
      this.jobs.set(jobs);
      this.available.set(account !== null);
      if (jobs.some((job) => !TERMINAL.has(job.status))) this.schedulePoll();
    } catch {
      this.available.set(false);
    } finally {
      this.loading.set(false);
    }
  }

  protected async saveProfile(event: Event): Promise<void> {
    event.preventDefault();
    const form = new FormData(event.target as HTMLFormElement);
    const draft: SearchProfile = {
      headline: String(form.get('headline') ?? '').trim(),
      seniority: String(form.get('seniority') ?? 'junior').trim() || 'junior',
      summary: String(form.get('summary') ?? '').trim(),
      skills: splitList(form.get('skills')),
      target_roles: splitList(form.get('target_roles')),
      search_terms: splitList(form.get('search_terms')),
      country: String(form.get('country') ?? '').trim() || 'España',
      onsite_cities: splitList(form.get('onsite_cities')),
      accepts_hybrid: form.get('accepts_hybrid') === 'on',
      remote_only: form.get('remote_only') === 'on',
      languages: splitList(form.get('languages')),
      max_years_experience: Math.min(30, Math.max(0, Number(form.get('max_years_experience')) || 0)),
    };
    this.saving.set(true);
    this.error.set('');
    this.message.set('');
    try {
      this.profile.set(await this.api.saveProfile(draft));
      this.message.set('Perfil guardado.');
    } catch (error) {
      this.error.set(
        error instanceof HttpErrorResponse && error.status === HTTP_VALIDATION
          ? 'Revisa el perfil: el titular y un resumen de al menos 10 caracteres son obligatorios.'
          : 'No se pudo guardar el perfil. Inténtalo de nuevo.',
      );
    } finally {
      this.saving.set(false);
    }
  }

  protected async startSearch(strategy: string): Promise<void> {
    this.starting.set(true);
    this.error.set('');
    this.message.set('');
    try {
      const job = await this.api.start(strategy as SearchStrategy);
      this.jobs.update((list) => [job, ...list]);
      this.account.set(await this.api.account());
      this.schedulePoll();
    } catch (error) {
      this.error.set(this.startError(error));
    } finally {
      this.starting.set(false);
    }
  }

  protected get busy(): boolean {
    return this.jobs().some((job) => !TERMINAL.has(job.status));
  }

  private startError(error: unknown): string {
    if (!(error instanceof HttpErrorResponse)) return 'No se pudo iniciar la búsqueda. Inténtalo de nuevo.';
    if (error.status === HTTP_PAYMENT_REQUIRED) return 'Has agotado las búsquedas de tu plan este mes.';
    if (error.status === HTTP_UNAUTHORIZED) return 'Tu sesión ha caducado. Vuelve a iniciar sesión.';
    if (error.status === HTTP_CONFLICT) {
      return this.profile() ? 'Ya tienes una búsqueda en curso.' : 'Guarda tu perfil antes de buscar.';
    }
    return 'No se pudo iniciar la búsqueda. Inténtalo de nuevo.';
  }

  private schedulePoll(): void {
    clearTimeout(this.timer);
    this.timer = setTimeout(() => void this.poll(), POLL_MS);
  }

  private async poll(): Promise<void> {
    if (this.destroyed) return;
    try {
      const jobs = await this.api.jobs();
      const finished = this.jobs().some((old) => !TERMINAL.has(old.status) && jobs.find((j) => j.id === old.id && TERMINAL.has(j.status)));
      this.jobs.set(jobs);
      if (finished) {
        this.account.set(await this.api.account());
        await this.store.load();
      }
      if (jobs.some((job) => !TERMINAL.has(job.status))) this.schedulePoll();
    } catch {
      this.schedulePoll();
    }
  }
}
