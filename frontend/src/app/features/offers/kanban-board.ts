import { ChangeDetectionStrategy, Component, input, output, signal } from '@angular/core';
import { KANBAN_STATUSES, KanbanStatus, Offer } from '../../core/models';
import { scoreTone } from '../../core/score';
import { inputValue } from '../../shared/dom';

export interface StatusChange {
  offer: Offer;
  status: KanbanStatus;
}

/** Tablero por estados con arrastrar y soltar (y un selector accesible en cada tarjeta). */
@Component({
  selector: 'app-kanban-board',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './kanban-board.html',
  styleUrl: './kanban-board.scss',
})
export class KanbanBoard {
  readonly offers = input.required<readonly Offer[]>();
  readonly moved = output<StatusChange>();

  protected readonly statuses = KANBAN_STATUSES;
  protected readonly dragging = signal<Offer | null>(null);
  protected readonly tone = scoreTone;
  protected readonly value = inputValue;

  protected inColumn(status: KanbanStatus): Offer[] {
    return this.offers().filter((o) => o.kanban_status === status);
  }

  protected drop(status: KanbanStatus, event: DragEvent): void {
    event.preventDefault();
    const offer = this.dragging();
    this.dragging.set(null);
    if (offer && offer.kanban_status !== status) this.moved.emit({ offer, status });
  }

  protected change(offer: Offer, status: string): void {
    this.moved.emit({ offer, status: status as KanbanStatus });
  }
}
