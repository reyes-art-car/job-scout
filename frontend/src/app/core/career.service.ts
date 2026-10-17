import { Injectable, signal } from '@angular/core';
import { CareerData, CvSnapshot, Evidence, LearningStage, SearchPreferences, emptyCareer, followUpDate, offerKey, safeEvidenceUrl } from './career';
import { validateCareer } from './career-validation';
import { KanbanStatus, Offer } from './models';
import { Origin } from './offer-analysis';
import { TechLevel } from './tech-catalog';

const STORAGE_KEY = 'jobscout.career.v1';
@Injectable({ providedIn: 'root' })
export class CareerService {
  private readonly current = signal<CareerData>(emptyCareer());
  readonly data = this.current.asReadonly();
  readonly notice = signal('');
  constructor() {
    try { const raw = localStorage.getItem(STORAGE_KEY); if (raw) this.current.set(validateCareer(JSON.parse(raw))); }
    catch { this.notice.set('No se ha podido leer el progreso guardado. Exporta una copia antes de borrar datos del navegador.'); }
  }
  private save(next: CareerData): void {
    const valid = validateCareer(next);
    this.current.set(valid);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(valid)); this.notice.set(''); }
    catch { this.notice.set('No se pudo guardar en el navegador. Exporta una copia antes de cerrar esta pestaña.'); }
  }
  addEvidence(input: Pick<Evidence, 'techId' | 'title' | 'description' | 'url'>): void {
    if (!input.title.trim() || !input.description.trim()) throw new Error('Añade un título y explica qué demuestra la evidencia.');
    const evidence: Evidence = { ...input, title: input.title.trim(), description: input.description.trim(), url: safeEvidenceUrl(input.url), id: crypto.randomUUID(), createdAt: new Date().toISOString() };
    this.save({ ...this.data(), evidence: [...this.data().evidence, evidence] });
  }
  removeEvidence(id: string): void {
    const data = this.data();
    const evidence = data.evidence.filter(e => e.id !== id);
    const skills = Object.fromEntries(Object.entries(data.skills).map(([tech, progress]) => [tech, progress.level === 'have' && !evidence.some(e => e.techId === tech) ? { ...progress, level: 'partial' as const } : progress]));
    this.save({ ...data, evidence, skills });
  }
  setSkill(id: string, stage: LearningStage, level: TechLevel): void {
    if (level === 'have' && !this.data().evidence.some(e => e.techId === id)) throw new Error('Adjunta una evidencia antes de incorporar esta competencia al CV.');
    this.save({ ...this.data(), skills: { ...this.data().skills, [id]: { stage, level } } });
  }
  setPreferences(preferences: SearchPreferences): void { this.save({ ...this.data(), preferences }); }
  correct(key: string, techId: string, origin: Origin | 'ignorar' | ''): void {
    const rows = { ...this.data().corrections[key] };
    if (origin) rows[techId] = origin; else delete rows[techId];
    this.save({ ...this.data(), corrections: { ...this.data().corrections, [key]: rows } });
  }
  recordStatus(offer: Offer, mode: string, status: KanbanStatus): void {
    if (offer.kanban_status === status) return;
    const event = { id: crypto.randomUUID(), offerKey: offerKey(offer, mode), title: offer.title, company: offer.company, from: offer.kanban_status, to: status, at: new Date().toISOString() };
    this.save({ ...this.data(), events: [...this.data().events, event].slice(-5000) });
  }
  saveCv(offer: Offer, mode: string, text: string, html: string, appliedOn: string | null): void {
    if (this.data().snapshots.length >= 300) throw new Error('Has alcanzado 300 versiones. Exporta una copia para conservarlas.');
    const snapshot: CvSnapshot = { id: crypto.randomUUID(), offerKey: offerKey(offer, mode), title: offer.title, company: offer.company, at: new Date().toISOString(), appliedOn, followUpOn: appliedOn ? followUpDate(appliedOn) : null, text, html };
    this.save({ ...this.data(), snapshots: [...this.data().snapshots, snapshot] });
  }
  exportBackup(): string { return JSON.stringify(this.data(), null, 2); }
  importBackup(raw: string): void {
    if (raw.length > 10000000) throw new Error('La copia supera el límite de 10 MB.');
    this.save(validateCareer(JSON.parse(raw)));
  }
}
