import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom, timeout } from 'rxjs';

export type SearchStrategy = 'general' | 'linkedin' | 'europa';
export type SearchStatus = 'queued' | 'running' | 'done' | 'failed';

export interface SearchProfile {
  headline: string;
  seniority: string;
  summary: string;
  skills: string[];
  target_roles: string[];
  search_terms: string[];
  country: string;
  onsite_cities: string[];
  accepts_hybrid: boolean;
  remote_only: boolean;
  languages: string[];
  max_years_experience: number;
}

export interface SearchJob {
  id: number;
  strategy: string;
  status: SearchStatus;
  created_at: string | null;
  finished_at: string | null;
  offers_added: number;
  offers_skipped: number;
  error: string | null;
}

const REQUEST_TIMEOUT_MS = 8000;
const STATUSES: readonly SearchStatus[] = ['queued', 'running', 'done', 'failed'];

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const int = (value: unknown): number => (typeof value === 'number' && Number.isFinite(value) ? Math.trunc(value) : 0);
const text = (value: unknown): string | null => (typeof value === 'string' ? value : null);

/** Valida una búsqueda recibida de la red antes de pintarla: la forma real, no la que se espera. */
export function parseJob(raw: unknown): SearchJob | null {
  if (!isRecord(raw) || typeof raw['id'] !== 'number') return null;
  const status = STATUSES.find((s) => s === raw['status']);
  if (!status) return null;
  return {
    id: raw['id'],
    strategy: text(raw['strategy']) ?? 'general',
    status,
    created_at: text(raw['created_at']),
    finished_at: text(raw['finished_at']),
    offers_added: int(raw['offers_added']),
    offers_skipped: int(raw['offers_skipped']),
    error: text(raw['error']),
  };
}

function parseProfile(raw: unknown): SearchProfile | null {
  if (!isRecord(raw) || typeof raw['headline'] !== 'string' || typeof raw['summary'] !== 'string') return null;
  const list = (key: string): string[] =>
    Array.isArray(raw[key]) ? (raw[key] as unknown[]).filter((v): v is string => typeof v === 'string') : [];
  return {
    headline: raw['headline'],
    seniority: text(raw['seniority']) ?? 'junior',
    summary: raw['summary'],
    skills: list('skills'),
    target_roles: list('target_roles'),
    search_terms: list('search_terms'),
    country: text(raw['country']) ?? 'España',
    onsite_cities: list('onsite_cities'),
    accepts_hybrid: raw['accepts_hybrid'] !== false,
    remote_only: raw['remote_only'] === true,
    languages: list('languages'),
    max_years_experience: int(raw['max_years_experience']),
  };
}

/** Perfil de búsqueda y búsquedas de ofertas contra la API. */
@Injectable({ providedIn: 'root' })
export class SearchService {
  private readonly http = inject(HttpClient);

  async profile(): Promise<SearchProfile | null> {
    return parseProfile(await this.get('/api/profile'));
  }

  async saveProfile(profile: SearchProfile): Promise<SearchProfile> {
    const saved = parseProfile(await firstValueFrom(this.http.put<unknown>('/api/profile', profile).pipe(timeout(REQUEST_TIMEOUT_MS))));
    if (!saved) throw new Error('Respuesta de la API no válida');
    return saved;
  }

  async jobs(): Promise<SearchJob[]> {
    const raw = await this.get('/api/searches');
    return Array.isArray(raw) ? raw.map(parseJob).filter((j): j is SearchJob => j !== null) : [];
  }

  async job(id: number): Promise<SearchJob | null> {
    return parseJob(await this.get(`/api/searches/${id}`));
  }

  async start(strategy: SearchStrategy): Promise<SearchJob> {
    const job = parseJob(await firstValueFrom(this.http.post<unknown>('/api/searches', { strategy }).pipe(timeout(REQUEST_TIMEOUT_MS))));
    if (!job) throw new Error('Respuesta de la API no válida');
    return job;
  }

  private get(url: string): Promise<unknown> {
    return firstValueFrom(this.http.get<unknown>(url).pipe(timeout(REQUEST_TIMEOUT_MS)));
  }
}
