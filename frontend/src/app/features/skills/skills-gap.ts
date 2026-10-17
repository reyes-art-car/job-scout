import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CareerService } from '../../core/career.service';
import { LearningStage, profileLevels } from '../../core/career';
import { ProfileService } from '../../core/profile.service';
import { inputValue } from '../../shared/dom';
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
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './skills-gap.html',
  styleUrl: './skills-gap.scss',
})
export class SkillsGap {
  private readonly store = inject(OfferStore);
  protected readonly career = inject(CareerService);
  private readonly profile = inject(ProfileService).profile;
  protected readonly value = inputValue;
  private readonly levels = computed(() => profileLevels(this.profile, this.career.data()));
  protected readonly progressMessage = signal('');

  protected readonly filter = signal<Filter>('todas');
  protected readonly filters: Filter[] = ['todas', 'A', 'B', 'C'];

  private readonly demand = computed(() => techDemand(this.store.offers(), this.levels()));

  protected readonly unlockMap = computed(() => {
    const map = new Map<string, number>();
    for (const offer of this.store.offers()) {
      const missing = analyzeOffer(offer, '', this.levels()).requirements.filter(
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

  protected stage(id: string, stage: string): void {
    try { this.career.setSkill(id, stage as LearningStage, this.levels()[id] ?? 'gap'); this.progressMessage.set('Progreso guardado. Completar una práctica no confirma automáticamente la competencia.'); }
    catch (error) { this.progressMessage.set(error instanceof Error ? error.message : 'No se pudo guardar.'); }
  }
  protected opportunities(id: string) {
    return this.store.offers().filter(offer => analyzeOffer(offer, '', this.levels()).requirements.some(r => r.tech.id === id));
  }
  protected readonly total = computed(() => this.store.offers().length);
}
