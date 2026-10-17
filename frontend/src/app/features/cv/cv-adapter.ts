import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs';
import { cvToWordHtml, downloadFile, slug } from '../../core/export';
import { CareerService } from '../../core/career.service';
import { analyzeForCareer, enrichedProfile, followUpDate, profileLevels } from '../../core/career';
import { MatchReview } from '../../shared/match-review';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Offer } from '../../core/models';
import { OfferStore } from '../../core/offer.store';
import { ProfileService } from '../../core/profile.service';
import { tailorCv } from '../../core/tailoring';
import { inputValue } from '../../shared/dom';
import { IconComponent } from '../../shared/icon.component';

@Component({
  selector: 'app-cv-adapter',
  imports: [IconComponent, MatchReview, FormsModule, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cv-adapter.html',
  styleUrl: './cv-adapter.scss',
})
export class CvAdapter {
  protected readonly store = inject(OfferStore);
  protected readonly career = inject(CareerService);
  protected readonly archiveMessage = signal('');
  protected readonly saving = signal(false);
  protected appliedOn = new Date().toLocaleDateString('sv-SE');
  protected readonly profile = inject(ProfileService).profile;
  protected readonly cvProfile = computed(() => enrichedProfile(this.profile, this.career.data()));

  protected readonly value = inputValue;

  protected readonly offers = computed(() =>
    [...this.store.offers()].sort((a, b) => b.compatibility - a.compatibility),
  );

  private readonly queryId = toSignal(
    inject(ActivatedRoute).queryParamMap.pipe(map((q) => Number(q.get('oferta')) || null)),
    { initialValue: null },
  );

  protected readonly selectedId = linkedSignal<number | null>(
    () => this.queryId() ?? this.offers()[0]?.id ?? null,
  );
  protected readonly description = signal('');
  protected readonly copied = signal(false);

  protected readonly offer = computed<Offer | undefined>(() => {
    const id = this.selectedId();
    return this.offers().find((o) => o.id === id);
  });

  protected readonly tailored = computed(() => {
    const offer = this.offer();
    if (!offer) return null;
    const data = this.career.data();
    return tailorCv(this.cvProfile(), offer, this.description(), profileLevels(this.profile, data), analyzeForCareer(this.profile, data, offer, this.store.mode(), this.description()));
  }, { equal: (a, b) => JSON.stringify(a) === JSON.stringify(b) });

  /** Título y resumen editables; se regeneran al cambiar de oferta o de texto. */
  protected readonly title = linkedSignal(() => this.tailored()?.title ?? '');
  protected readonly summary = linkedSignal(() => this.tailored()?.summary ?? '');

  protected pick(value: string): void {
    this.selectedId.set(Number(value));
  }

  protected asText(): string {
    const cv = this.tailored();
    if (!cv) return '';
    const p = this.cvProfile();
    return [
      p.name.toUpperCase(),
      this.title(),
      `${p.location} | ${p.email} | ${p.linkedin}`,
      '',
      'PERFIL PROFESIONAL',
      this.summary(),
      '',
      'EXPERIENCIA Y PROYECTOS',
      `${p.company.toUpperCase()} | ${p.role} — ${p.period}`,
      p.project,
      ...cv.bullets.map((b) => `• ${b.text}`),
      '',
      'COMPETENCIAS TÉCNICAS',
      ...cv.groups.map((g) => `${g.label}: ${g.items.map((i) => i.text).join(', ')}`),
      '',
      'FORMACIÓN',
      `${p.education.degree} | ${p.education.school} | ${p.education.years}`,
      '',
      'IDIOMAS',
      `${p.languages.name} — ${p.languages.detail}`,
    ].join('\n');
  }

  protected async copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(this.asText());
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    } catch {
      // portapapeles no disponible (contexto no seguro): el usuario puede seleccionar el texto
    }
  }

  protected downloadWord(): void {
    const cv = this.tailored();
    const offer = this.offer();
    if (!cv || !offer) return;
    const edited = { ...cv, title: this.title(), summary: this.summary() };
    downloadFile(
      `CV_${offer.code}_${slug(offer.company)}_${slug(offer.title)}.doc`,
      cvToWordHtml(this.cvProfile(), edited),
      'application/msword',
    );
  }

  protected async archive(sent: boolean): Promise<void> {
    const offer = this.offer();
    const cv = this.tailored();
    if (!offer || !cv || this.saving()) return;
    const mode = this.store.mode();
    const text = this.asText();
    const html = cvToWordHtml(this.cvProfile(), { ...cv, title: this.title(), summary: this.summary() });
    this.saving.set(true);
    try {
      const appliedOn = sent ? this.validApplicationDate() : null;
      if (appliedOn && offer.kanban_status === 'Pendiente') await this.store.setStatus(offer, 'Aplicado');
      this.career.saveCv(offer, mode, text, html, appliedOn);
      this.archiveMessage.set(sent ? 'Envío registrado y versión guardada. No se ha enviado nada al portal de empleo.' : 'Versión guardada como borrador.');
    } catch (error) { this.archiveMessage.set(error instanceof Error ? error.message : 'No se pudo guardar. Inténtalo de nuevo.'); }
    finally { this.saving.set(false); }
  }

  private validApplicationDate(): string {
    followUpDate(this.appliedOn);
    if (this.appliedOn > new Date().toLocaleDateString('sv-SE')) throw new Error('El envío no puede estar en el futuro.');
    return this.appliedOn;
  }

  protected print(): void {
    window.print();
  }
}
