import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { downloadFile, offersToCsv } from '../../core/export';
import { KANBAN_STATUSES, KanbanStatus, NewOffer, Offer, Priority } from '../../core/models';
import { EMPTY_QUERY, OfferQuery, SortKey, applyQuery } from '../../core/offer-query';
import { OfferStore } from '../../core/offer.store';
import { scoreTone } from '../../core/score';
import { inputValue } from '../../shared/dom';
import { IconComponent } from '../../shared/icon.component';
import { KanbanBoard, StatusChange } from './kanban-board';
import { OfferForm } from './offer-form';

type View = 'tabla' | 'kanban';

const MAX_CHIPS = 6;

@Component({
  selector: 'app-offers',
  imports: [RouterLink, IconComponent, OfferForm, KanbanBoard],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './offers.html',
  styleUrl: './offers.scss',
})
export class Offers {
  private readonly store = inject(OfferStore);

  protected readonly statuses = KANBAN_STATUSES;
  protected readonly tone = scoreTone;
  protected readonly value = inputValue;

  protected readonly view = signal<View>('tabla');
  protected readonly showForm = signal(false);
  protected readonly query = signal<OfferQuery>(EMPTY_QUERY);
  protected readonly filtered = computed(() => applyQuery(this.store.offers(), this.query()));

  protected patchQuery(patch: Partial<OfferQuery>): void {
    this.query.update((current) => ({ ...current, ...patch }));
  }

  protected setStatusFilter(value: string): void {
    this.patchQuery({ status: value as KanbanStatus | '' });
  }

  protected setPriorityFilter(value: string): void {
    this.patchQuery({ priority: value as Priority | '' });
  }

  protected setSort(value: string): void {
    this.patchQuery({ sort: value as SortKey });
  }

  protected techList(text: string): string[] {
    return text
      .split(/[,;]/)
      .map((t) => t.trim())
      .filter(Boolean)
      .slice(0, MAX_CHIPS);
  }

  protected async changeStatus(offer: Offer, status: string): Promise<void> {
    await this.store.setStatus(offer, status as KanbanStatus);
  }

  protected async move({ offer, status }: StatusChange): Promise<void> {
    await this.store.setStatus(offer, status);
  }

  protected async create(draft: NewOffer): Promise<void> {
    await this.store.add(draft);
    this.showForm.set(false);
  }

  protected exportCsv(): void {
    const date = new Date().toISOString().slice(0, 10);
    downloadFile(`ofertas_${date}.csv`, offersToCsv(this.filtered()), 'text/csv');
  }
}
