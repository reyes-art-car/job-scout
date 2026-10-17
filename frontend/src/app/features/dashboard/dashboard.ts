import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CareerService } from '../../core/career.service';
import { profileLevels } from '../../core/career';
import { ProfileService } from '../../core/profile.service';
import { techDemand } from '../../core/market';
import { KANBAN_STATUSES } from '../../core/models';
import { OfferStore } from '../../core/offer.store';
import { scoreTone, statusChipClass } from '../../core/score';
import { IconComponent } from '../../shared/icon.component';

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard {
  private readonly store = inject(OfferStore);
  private readonly career = inject(CareerService);
  private readonly profile = inject(ProfileService).profile;

  protected readonly stats = this.store.stats;
  protected readonly tone = scoreTone;
  protected readonly statusClass = statusChipClass;
  protected readonly statuses = KANBAN_STATUSES;

  protected readonly applied = computed(() => {
    const s = this.stats().byStatus;
    return s.Aplicado + s.Entrevista + s.Oferta;
  });

  protected readonly funnel = computed(() => {
    const { byStatus, total } = this.stats();
    return KANBAN_STATUSES.map((status) => ({
      status,
      count: byStatus[status],
      pct: total === 0 ? 0 : Math.round((byStatus[status] / total) * 100),
    }));
  });

  protected readonly histogram = computed(() => {
    const buckets = [
      { label: '< 60', min: 0, max: 59 },
      { label: '60–69', min: 60, max: 69 },
      { label: '70–79', min: 70, max: 79 },
      { label: '80–89', min: 80, max: 89 },
      { label: '90+', min: 90, max: 100 },
    ].map((b) => ({
      ...b,
      count: this.store.offers().filter((o) => o.compatibility >= b.min && o.compatibility <= b.max).length,
    }));
    const max = Math.max(...buckets.map((b) => b.count), 1);
    return buckets.map((b) => ({ ...b, height: Math.round((b.count / max) * 100) }));
  });

  protected readonly demand = computed(() =>
    techDemand(this.store.offers(), profileLevels(this.profile, this.career.data()))
      .filter((d) => d.tech.id !== 'english')
      .slice(0, 10),
  );

  protected readonly next = computed(() =>
    this.store
      .offers()
      .filter((o) => o.kanban_status === 'Pendiente')
      .sort((a, b) => b.compatibility - a.compatibility)
      .slice(0, 5),
  );
}
