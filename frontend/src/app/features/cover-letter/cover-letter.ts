import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { map } from 'rxjs';
import { Tone, buildCoverLetter, letterToText } from '../../core/cover-letter';
import { downloadFile, letterToWordHtml, slug } from '../../core/export';
import { OfferStore } from '../../core/offer.store';
import { ProfileService } from '../../core/profile.service';
import { analyzeOffer } from '../../core/tailoring';
import { IconComponent } from '../../shared/icon.component';

const MONTHS = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
];

@Component({
  selector: 'app-cover-letter',
  imports: [IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cover-letter.html',
  styleUrl: './cover-letter.scss',
})
export class CoverLetter {
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
  protected readonly tone = signal<Tone>('formal');
  protected readonly mentionGaps = signal(false);
  protected readonly availability = signal('de inmediato');
  protected readonly description = signal('');
  protected readonly copied = signal(false);

  protected readonly offer = computed(() => this.offers().find((o) => o.id === this.selectedId()));

  protected readonly gaps = computed(() => {
    const offer = this.offer();
    return offer ? analyzeOffer(offer, this.description()).missing.slice(0, 3) : [];
  });

  private readonly generated = computed(() => {
    const offer = this.offer();
    if (!offer) return '';
    const letter = buildCoverLetter(this.profile, offer, {
      tone: this.tone(),
      mentionGaps: this.mentionGaps(),
      availability: this.availability(),
      description: this.description(),
    });
    const now = new Date();
    const dateLine = `Sevilla, ${now.getDate()} de ${MONTHS[now.getMonth()]} de ${now.getFullYear()}`;
    return letterToText(letter, offer.company, dateLine);
  });

  /** Texto editable: se regenera cuando cambian las opciones y se puede retocar a mano. */
  protected readonly text = linkedSignal(() => this.generated());
  protected readonly words = computed(() => this.text().trim().split(/\s+/).filter(Boolean).length);

  protected pick(value: string): void {
    this.selectedId.set(Number(value));
  }

  protected async copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(this.text());
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    } catch {
      // portapapeles no disponible
    }
  }

  protected downloadWord(): void {
    const offer = this.offer();
    if (!offer) return;
    downloadFile(
      `Carta_${offer.code}_${slug(offer.company)}_${slug(offer.title)}.doc`,
      letterToWordHtml(this.profile, this.text()),
      'application/msword',
    );
  }
}
