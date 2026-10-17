import { ChangeDetectionStrategy, Component, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NewOffer } from '../../core/models';
import { analyzeOffer } from '../../core/offer-analysis';
import { safeHttpUrl } from '../../core/offer-validation';
import { scoreTone } from '../../core/score';
import { IconComponent } from '../../shared/icon.component';

const MAX_TEXT = 255;
const MAX_LONG = 4000;

const emptyDraft = (): NewOffer => ({
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

/** Formulario de alta de oferta. Solo recoge y valida datos: guardarlos es cosa de quien lo usa. */
@Component({
  selector: 'app-offer-form',
  imports: [FormsModule, IconComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './offer-form.html',
  styleUrl: './offer-form.scss',
})
export class OfferForm {
  readonly saved = output<NewOffer>();
  readonly cancelled = output<void>();

  protected draft: NewOffer = emptyDraft();
  protected readonly estimate = signal(0);
  protected readonly urlInvalid = signal(false);
  protected readonly tone = scoreTone;
  protected readonly maxText = MAX_TEXT;
  protected readonly maxLong = MAX_LONG;

  protected updateEstimate(): void {
    this.estimate.set(analyzeOffer(this.draft).coverage);
  }

  protected validateUrl(): void {
    this.urlInvalid.set(!!this.draft.url?.trim() && safeHttpUrl(this.draft.url.trim()) === null);
  }

  protected submit(): void {
    const d = this.draft;
    const url = d.url?.trim() ? safeHttpUrl(d.url.trim()) : null;
    if (!d.title.trim() || !d.company.trim() || (d.url?.trim() && url === null)) {
      this.validateUrl();
      return;
    }
    const analysis = analyzeOffer(d);
    this.saved.emit({
      ...d,
      title: d.title.trim(),
      company: d.company.trim(),
      url,
      salary: d.salary?.trim() ? d.salary.trim() : null,
      compatibility: d.compatibility > 0 ? d.compatibility : analysis.coverage,
      requirements_met: analysis.matched.map((r) => `${r.tech.name} ✓`).join('  '),
      requirements_missing: analysis.missing.map((r) => r.tech.name).join(', ') || 'Ninguno',
      score_reason: 'Estimación automática por cobertura de palabras clave del catálogo.',
    });
    this.draft = emptyDraft();
    this.estimate.set(0);
  }
}
