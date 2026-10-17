import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { downloadFile, offersToCsv } from '../../core/export';
import { KANBAN_STATUSES, KanbanStatus, NewOffer, Offer } from '../../core/models';
import { OfferStore } from '../../core/offer.store';
import { analyzeOffer } from '../../core/tailoring';
import { IconComponent } from '../../shared/icon.component';

type View = 'tabla' | 'kanban';
type SortKey = 'compat' | 'fecha' | 'empresa';

const EMPTY_DRAFT = (): NewOffer => ({
  title: '',
  company: '',
  portal: 'LinkedIn',
  url: '',
  published_date: new Date().toISOString().slice(0, 10),
  location: '',
  modality: 'Remoto 100%',
  contract_type: 'No especificado',
  salary: '',
  experience_required: '',
  mandatory_tech: '',
  desirable_tech: '',
  requirements_met: '',
  requirements_missing: '',
  score_reason: '',
  compatibility: 0,
  kanban_status: 'Pendiente',
  notes: '',
});

@Component({
  selector: 'app-offers',
  imports: [FormsModule, RouterLink, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './offers.html',
  styleUrl: './offers.scss',
})
export class Offers {
  private readonly store = inject(OfferStore);

  protected readonly statuses = KANBAN_STATUSES;
  protected readonly view = signal<View>('tabla');
  protected readonly query = signal('');
  protected readonly statusFilter = signal<KanbanStatus | ''>('');
  protected readonly priorityFilter = signal<'' | 'Alta' | 'Secundaria'>('');
  protected readonly minCompat = signal(0);
  protected readonly sort = signal<SortKey>('compat');
  protected readonly showForm = signal(false);
  protected readonly draggingId = signal<number | null>(null);

  protected draft: NewOffer = EMPTY_DRAFT();
  protected readonly estimate = signal(0);

  protected readonly filtered = computed(() => {
    const q = this.query().trim().toLowerCase();
    const status = this.statusFilter();
    const priority = this.priorityFilter();
    const min = this.minCompat();
    const sortKey = this.sort();
    const list = this.store.offers().filter(
      (o) =>
        (!q || `${o.title} ${o.company} ${o.mandatory_tech}`.toLowerCase().includes(q)) &&
        (!status || o.kanban_status === status) &&
        (!priority || o.priority === priority) &&
        o.compatibility >= min,
    );
    return list.sort((a, b) =>
      sortKey === 'compat'
        ? b.compatibility - a.compatibility
        : sortKey === 'fecha'
          ? (b.published_date ?? '').localeCompare(a.published_date ?? '')
          : a.company.localeCompare(b.company),
    );
  });

  protected readonly columns = computed(() =>
    KANBAN_STATUSES.map((status) => ({
      status,
      offers: this.filtered().filter((o) => o.kanban_status === status),
    })),
  );

  protected tone(score: number): string {
    return score >= 80 ? 'high' : score >= 70 ? 'mid' : 'low';
  }

  protected techList(text: string): string[] {
    return text
      .split(/[,;]/)
      .map((t) => t.trim())
      .filter(Boolean)
      .slice(0, 6);
  }

  protected async changeStatus(offer: Offer, status: string): Promise<void> {
    await this.store.setStatus(offer, status as KanbanStatus);
  }

  protected onDrop(status: KanbanStatus, event: DragEvent): void {
    event.preventDefault();
    const id = this.draggingId();
    this.draggingId.set(null);
    const offer = id === null ? undefined : this.store.byId(id);
    if (offer && offer.kanban_status !== status) void this.store.setStatus(offer, status);
  }

  protected exportCsv(): void {
    const date = new Date().toISOString().slice(0, 10);
    downloadFile(`ofertas_${date}.csv`, offersToCsv(this.filtered()), 'text/csv');
  }

  protected updateEstimate(): void {
    const analysis = analyzeOffer(this.draft);
    this.estimate.set(analysis.coverage);
  }

  protected async save(): Promise<void> {
    const d = this.draft;
    if (!d.title.trim() || !d.company.trim()) return;
    const analysis = analyzeOffer(d);
    await this.store.add({
      ...d,
      url: d.url?.trim() ? d.url.trim() : null,
      salary: d.salary?.trim() ? d.salary : null,
      compatibility: d.compatibility > 0 ? d.compatibility : analysis.coverage,
      requirements_met: analysis.matched.map((r) => `${r.tech.name} ✓`).join('  '),
      requirements_missing: analysis.missing.map((r) => r.tech.name).join(', ') || 'Ninguno',
      score_reason: 'Estimación automática por cobertura de palabras clave del catálogo.',
    });
    this.draft = EMPTY_DRAFT();
    this.estimate.set(0);
    this.showForm.set(false);
  }
}
