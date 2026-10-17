import { ChangeDetectionStrategy, Component, computed, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { analyzeForCareer, evidenceSources, fitWarnings, offerKey } from '../core/career';
import { CareerService } from '../core/career.service';
import { Offer, Profile } from '../core/models';
import { Origin, Requirement, extractRequirements } from '../core/offer-analysis';
import { TECH_CATALOG, detectTechs } from '../core/tech-catalog';
import { inputValue } from './dom';

@Component({
  selector: 'app-match-review', imports: [RouterLink], changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <section class="card no-print">
      <span class="eyebrow">POR QUÉ ENCAJA</span>
      <h2>Requisitos, sin caja negra</h2>
      <p><strong>{{ analysis().coverage }}% de cobertura técnica</strong> sobre {{ analysis().requirements.length }} requisitos reconocidos.</p>
      <p class="small muted">No es una probabilidad de entrevista ni una evaluación ATS. Obligatorio pesa 3; deseable, 1; texto, 1,5; inglés, 0,5. Parcial suma la mitad. Los requisitos fuera del catálogo no se puntúan.</p>
      <details>
        <summary>Revisar y corregir el análisis</summary>
        @for (r of analysis().requirements; track r.tech.id) {
          <article class="requirement">
            <div class="actions"><strong>{{ r.tech.name }}</strong><span class="chip">Peso {{ r.weight }}</span><span class="chip">{{ r.tech.level === 'have' ? 'Declarada' : r.tech.level === 'partial' ? 'Parcial' : 'Pendiente' }}</span></div>
            <p class="small">Origen: {{ r.origin }}. Fuente: {{ source(r) }}</p>
            @for (source of sources(r.tech.id); track source) { <p class="small muted">{{ source }}</p> }
            @if (!sources(r.tech.id).length) { <p class="small muted">Sin evidencia en tu perfil.</p> }
            <label>Tu revisión del requisito
              <select [value]="corrections()[r.tech.id] || ''" (change)="correct(r.tech.id, value($event))">
                <option value="">Detección original</option><option value="obligatoria">Obligatorio</option><option value="deseable">Deseable</option><option value="texto">Mencionado, sin confirmar</option><option value="ignorar">No es un requisito</option>
              </select>
            </label>
          </article>
        } @empty { <p class="empty">No hay requisitos reconocidos. Pega el texto del anuncio y revisa manualmente lo que falta.</p> }
        @for (id of ignored(); track id) { <button class="btn" type="button" (click)="correct(id, '')">Restaurar {{ techName(id) }}</button> }
        <a routerLink="/mi-perfil">Revisar mis competencias y evidencias →</a>
      </details>
      <h3>Condiciones por confirmar</h3>
      @for (warning of warnings(); track warning.kind) { <p class="callout">{{ warning.text }}</p> }
      @if (!warnings().length) { <p class="small muted">Sin alertas con los datos disponibles. Confirma las condiciones con la empresa.</p> }
      <a class="small" routerLink="/mi-perfil">Cambiar experiencia y preferencias</a>
    </section>`,
  styles: [`:host{display:block}.requirement{padding:16px 0;border-bottom:1px solid var(--border)}p{margin:10px 0}h3{margin-top:20px}summary{cursor:pointer;padding:14px 0;font-weight:600}label{margin-top:10px}.callout{padding:12px;border-left:3px solid var(--warn);background:var(--warn-soft);border-radius:6px}`],
})
export class MatchReview {
  readonly offer = input.required<Offer>();
  readonly profile = input.required<Profile>();
  readonly mode = input.required<string>();
  readonly description = input('');
  protected readonly career = inject(CareerService);
  protected readonly value = inputValue;
  protected readonly key = computed(() => offerKey(this.offer(), this.mode()));
  protected readonly corrections = computed(() => this.career.data().corrections[this.key()] ?? {});
  protected readonly analysis = computed(() => analyzeForCareer(this.profile(), this.career.data(), this.offer(), this.mode(), this.description()));
  protected readonly warnings = computed(() => fitWarnings(this.offer(), this.career.data().preferences));
  protected readonly ignored = computed(() => Object.keys(this.corrections()).filter(id => this.corrections()[id] === 'ignorar'));
  protected sources(id: string) { return evidenceSources(this.profile(), this.career.data(), id); }
  protected techName(id: string) { return TECH_CATALOG.find(t => t.id === id)?.name ?? id; }
  protected source(r: Requirement): string {
    const original = extractRequirements(this.offer(), this.description()).find(item => item.tech.id === r.tech.id);
    if (original?.origin === 'obligatoria') return this.offer().mandatory_tech || 'Marcado por ti; verifica el anuncio.';
    if (original?.origin === 'deseable') return this.offer().desirable_tech || 'Marcado por ti; verifica el anuncio.';
    return detectTechs(this.description()).some(t => t.id === r.tech.id) ? this.description() : this.offer().title;
  }
  protected correct(id: string, origin: string): void { this.career.correct(this.key(), id, origin as Origin | 'ignorar' | ''); }
}
