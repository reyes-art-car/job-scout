import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs';
import { cvToWordHtml, downloadFile, slug } from '../../core/export';
import { Offer } from '../../core/models';
import { OfferStore } from '../../core/offer.store';
import { ProfileService } from '../../core/profile.service';
import { tailorCv } from '../../core/tailoring';
import { IconComponent } from '../../shared/icon.component';

@Component({
  selector: 'app-cv-adapter',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cv-adapter.html',
  styleUrl: './cv-adapter.scss',
})
export class CvAdapter {
  private readonly store = inject(OfferStore);
  protected readonly profile = inject(ProfileService).profile;

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
    return offer ? tailorCv(this.profile, offer, this.description()) : null;
  });

  /** Título y resumen editables; se regeneran al cambiar de oferta o de texto. */
  protected readonly title = linkedSignal(() => this.tailored()?.title ?? '');
  protected readonly summary = linkedSignal(() => this.tailored()?.summary ?? '');

  protected pick(value: string): void {
    this.selectedId.set(Number(value));
  }

  protected asText(): string {
    const cv = this.tailored();
    if (!cv) return '';
    const p = this.profile;
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
      cvToWordHtml(this.profile, edited),
      'application/msword',
    );
  }

  protected print(): void {
    window.print();
  }
}
