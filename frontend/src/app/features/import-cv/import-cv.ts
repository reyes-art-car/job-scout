import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { CvFileError, MAX_CV_BYTES, extractCvText } from '../../core/cv-text';
import { parseCv } from '../../core/cv-parser';
import { OfferStorage } from '../../core/gateways/offer-storage';
import { Profile, SkillGroup } from '../../core/models';
import { OfferStore } from '../../core/offer.store';
import { ProfileService } from '../../core/profile.service';
import { detectTechs } from '../../core/tech-catalog';
import { IconComponent } from '../../shared/icon.component';
import { PublicShell } from '../../shared/public-shell';

type Step = 'upload' | 'reading' | 'review';

/** Texto editable «Categoría: A, B, C» (una línea por grupo) ⇄ grupos de competencias del perfil. */
const groupsToText = (groups: SkillGroup[]): string => groups.map((g) => `${g.label}: ${g.content}`).join('\n');
const textToGroups = (value: string): SkillGroup[] =>
  value
    .split('\n')
    .map((line) => line.split(':'))
    .filter((parts) => parts.length >= 2)
    .map(([label, ...rest]) => ({ label: label.trim(), content: rest.join(':').trim() }))
    .filter((g) => g.label && g.content);

@Component({
  selector: 'app-import-cv',
  imports: [FormsModule, RouterLink, IconComponent, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './import-cv.html',
  styleUrl: './import-cv.scss',
})
export class ImportCv {
  private readonly router = inject(Router);
  private readonly profiles = inject(ProfileService);
  private readonly store = inject(OfferStore);
  private readonly offerStorage = inject(OfferStorage);

  protected readonly maxMb = MAX_CV_BYTES / 1024 / 1024;
  protected readonly step = signal<Step>('upload');
  protected readonly error = signal('');
  protected readonly dragging = signal(false);
  protected readonly fileName = signal('');
  protected readonly isCustom = this.profiles.isCustom;

  /** Perfil propuesto, editable en el formulario de revisión. */
  protected draft!: Profile;
  protected bulletsText = '';
  protected skillsText = '';
  protected skillsEdited = false;
  protected readonly detected = signal<string[]>([]);

  protected readonly canSave = computed(() => this.step() === 'review');

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(false);
    const file = event.dataTransfer?.files?.[0];
    if (file) void this.read(file);
  }

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(true);
  }

  protected onPick(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) void this.read(file);
  }

  protected async read(file: File): Promise<void> {
    this.error.set('');
    this.fileName.set(file.name);
    this.step.set('reading');
    try {
      const profile = parseCv(await extractCvText(file));
      this.draft = profile;
      this.bulletsText = profile.bullets.map((b) => b.text).join('\n');
      this.skillsText = groupsToText(profile.skills.fullstack);
      this.skillsEdited = false;
      this.detected.set(profile.skills.fullstack.flatMap((g) => g.content.split(', ')));
      this.step.set('review');
    } catch (error) {
      this.error.set(error instanceof CvFileError ? error.message : 'No se ha podido leer el archivo.');
      this.step.set('upload');
    }
  }

  protected async save(): Promise<void> {
    this.error.set('');
    const d = this.draft;
    const bullets = this.bulletsText
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
    const edited = textToGroups(this.skillsText);
    const profile: Profile = {
      ...d,
      bullets: bullets.map((text) => ({ text, tags: detectTechs(text).map((t) => t.id) })),
      skills: this.skillsEdited ? { backend_first: edited, fullstack: edited, frontend_first: edited } : d.skills,
    };
    if (!this.profiles.saveCustom(profile)) {
      this.error.set('Indica al menos tu nombre y alguna tecnología o logro. Si ya lo has hecho, es posible que tu navegador no permita guardar datos.');
      return;
    }
    // Las ofertas de ejemplo guardadas se puntuaron con otro perfil: se vuelven a calcular con este.
    this.offerStorage.clear();
    await this.store.load();
    await this.router.navigateByUrl('/panel');
  }
}
