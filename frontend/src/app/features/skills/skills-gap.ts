import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { TechDemand, techDemand } from '../../core/market';
import { OfferStore } from '../../core/offer.store';
import { analyzeOffer } from '../../core/offer-analysis';

type Filter = 'todas' | 'A' | 'B' | 'C';

interface GapRow extends TechDemand {
  /** Ofertas del tracker en las que esta es la ÚNICA tecnología obligatoria que falta. */
  unlocks: number;
}

@Component({
  selector: 'app-skills-gap',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './skills-gap.html',
  styleUrl: './skills-gap.scss',
})
export class SkillsGap {
  private readonly store = inject(OfferStore);

  protected readonly filter = signal<Filter>('todas');
  protected readonly filters: Filter[] = ['todas', 'A', 'B', 'C'];

  private readonly demand = computed(() => techDemand(this.store.offers()));

  protected readonly unlockMap = computed(() => {
    const map = new Map<string, number>();
    for (const offer of this.store.offers()) {
      const missing = analyzeOffer(offer).requirements.filter(
        (r) => r.tech.level === 'gap' && r.origin === 'obligatoria',
      );
      if (missing.length === 1) {
        const id = missing[0].tech.id;
        map.set(id, (map.get(id) ?? 0) + 1);
      }
    }
    return map;
  });

  protected readonly gaps = computed<GapRow[]>(() =>
    this.demand()
      .filter((d) => d.tech.level !== 'have')
      .map((d) => ({ ...d, unlocks: this.unlockMap().get(d.tech.id) ?? 0 }))
      .sort((a, b) => b.unlocks - a.unlocks || b.mandatory * 2 + b.offers - (a.mandatory * 2 + a.offers)),
  );

  protected readonly visible = computed(() => {
    const f = this.filter();
    return this.gaps().filter((g) => f === 'todas' || g.tech.priority === f);
  });

  protected readonly strengths = computed(() =>
    this.demand()
      .filter((d) => d.tech.level === 'have' && d.tech.id !== 'english')
      .slice(0, 12),
  );

  protected readonly total = computed(() => this.store.offers().length);
}
