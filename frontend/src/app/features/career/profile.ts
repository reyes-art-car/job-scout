import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CareerService } from '../../core/career.service';
import { LearningStage, evidenceSources, profileLevels } from '../../core/career';
import { ProfileService } from '../../core/profile.service';
import { TECH_CATALOG, TechLevel } from '../../core/tech-catalog';
import { downloadFile } from '../../core/export';

@Component({
  selector: 'app-career-profile', imports: [FormsModule], changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './profile.html', styleUrl: './career.scss'
})
export class CareerProfile {
  protected readonly career = inject(CareerService);
  private readonly profile = inject(ProfileService).profile;
  protected readonly catalog = TECH_CATALOG;
  protected readonly levels = computed(() => profileLevels(this.profile, this.career.data()));
  protected readonly message = signal('');
  protected readonly search = signal('');
  protected readonly visibleTechs = computed(() => TECH_CATALOG.filter(t => t.name.toLowerCase().includes(this.search().toLowerCase())));
  private readonly initialTech = inject(ActivatedRoute).snapshot.queryParamMap.get('tech');
  protected techId = TECH_CATALOG.find(t => t.id === this.initialTech)?.id ?? TECH_CATALOG[0].id;
  protected title = '';
  protected description = '';
  protected url = '';
  protected years = this.career.data().preferences.experienceYears;
  protected location = this.career.data().preferences.location;
  protected remoteOnly = this.career.data().preferences.remoteOnly;
  protected backup = '';
  protected confirmImport = false;
  protected addEvidence(): void {
    try { this.career.addEvidence({ techId: this.techId, title: this.title, description: this.description, url: this.url }); this.title = this.description = this.url = ''; this.message.set('Evidencia guardada. Puedes confirmar la competencia cuando estés preparada para defenderla.'); }
    catch (error) { this.message.set(error instanceof Error ? error.message : 'No se pudo guardar.'); }
  }
  protected setLevel(id: string, value: string): void {
    const stage: LearningStage = this.career.data().skills[id]?.stage ?? 'pendiente';
    try { this.career.setSkill(id, stage, value as TechLevel); this.message.set('Nivel actualizado.'); }
    catch (error) { this.message.set(error instanceof Error ? error.message : 'No se pudo actualizar.'); }
  }
  protected canConfirm(id: string): boolean { return this.career.data().evidence.some(e => e.techId === id); }
  protected sources(id: string): string[] { return evidenceSources(this.profile, this.career.data(), id); }
  protected name(id: string): string { return TECH_CATALOG.find(t => t.id === id)?.name ?? id; }
  protected preferences(): void {
    try { this.career.setPreferences({ experienceYears: this.years, location: this.location.trim(), remoteOnly: this.remoteOnly }); this.message.set('Preferencias guardadas.'); }
    catch (error) { this.message.set(error instanceof Error ? error.message : 'Revisa las preferencias.'); }
  }
  protected export(): void { downloadFile('jobscout-progreso.json', this.career.exportBackup(), 'application/json'); }
  protected import(): void {
    if (!this.confirmImport) return;
    try { this.career.importBackup(this.backup); this.backup = ''; this.confirmImport = false; const p = this.career.data().preferences; this.years = p.experienceYears; this.location = p.location; this.remoteOnly = p.remoteOnly; this.message.set('Copia restaurada.'); }
    catch (error) { this.message.set(error instanceof Error ? error.message : 'Copia no válida.'); }
  }
}
