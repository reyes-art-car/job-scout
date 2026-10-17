import { ChangeDetectionStrategy, Component, computed, inject, signal, LOCALE_ID } from '@angular/core';
import { DatePipe, registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';
import { FormsModule } from '@angular/forms';
import { CareerService } from '../../core/career.service';
import { CvSnapshot } from '../../core/career';
import { downloadFile } from '../../core/export';

registerLocaleData(localeEs);

@Component({
  selector: 'app-application-history', providers: [{ provide: LOCALE_ID, useValue: 'es' }], imports: [DatePipe, FormsModule], changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './history.html', styleUrl: './career.scss'
})
export class ApplicationHistory {
  protected readonly career = inject(CareerService);
  protected readonly query = signal('');
  protected readonly today = new Date().toLocaleDateString('sv-SE');
  protected readonly snapshots = computed(() => [...this.career.data().snapshots].reverse().filter(s => `${s.title} ${s.company}`.toLowerCase().includes(this.query().toLowerCase())));
  protected readonly events = computed(() => [...this.career.data().events].reverse().filter(e => `${e.title} ${e.company}`.toLowerCase().includes(this.query().toLowerCase())));
  protected readonly sent = computed(() => this.career.data().snapshots.filter(s => s.appliedOn !== null).length);
  protected readonly interviews = computed(() => new Set(this.career.data().events.filter(e => e.to === 'Entrevista').map(e => e.offerKey)).size);
  protected currentStatus(snapshot: CvSnapshot): string {
    return [...this.career.data().events].reverse().find(e => e.offerKey === snapshot.offerKey)?.to ?? 'Sin cambios registrados';
  }
  protected download(snapshot: CvSnapshot): void { downloadFile(`CV_${snapshot.id}.txt`, snapshot.text, 'text/plain'); }
}
