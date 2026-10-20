import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';

const PATHS: Record<string, string> = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  briefcase: 'M3 7h18v13H3zM8 7V4h8v3M3 13h18',
  file: 'M6 2h9l5 5v15H6zM14 2v6h6M9 13h7M9 17h7',
  mail: 'M3 5h18v14H3zM3 6l9 7 9-7',
  chart: 'M4 20V10M10 20V4M16 20v-8M22 20H2',
  download: 'M12 3v12M7 11l5 5 5-5M4 21h16',
  plus: 'M12 5v14M5 12h14',
  search: 'M11 4a7 7 0 100 14 7 7 0 000-14zM21 21l-5-5',
  check: 'M4 12l5 5L20 6',
  x: 'M5 5l14 14M19 5L5 19',
  copy: 'M9 9h11v11H9zM5 15V4h11',
  print: 'M6 9V3h12v6M6 18H3v-8h18v8h-3M6 14h12v7H6z',
  kanban: 'M4 4h5v16H4zM10 4h5v10h-5zM16 4h4v13h-4z',
  list: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  link: 'M10 14a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1M14 10a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1',
  steps: 'M3 20h18M5 20v-5h4v5M10 20v-9h4v9M15 20V6h4v14',
  target: 'M12 3a9 9 0 100 18 9 9 0 000-18zM12 8a4 4 0 100 8 4 4 0 000-8zM12 12h.01',
  alert: 'M12 3l10 18H2zM12 10v5M12 18h.01',
  sparkle: 'M12 3l2 6 6 2-6 2-2 6-2-6-6-2 6-2zM19 3v4M17 5h4',
};

@Component({
  selector: 'app-icon',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<svg
    [attr.width]="size()"
    [attr.height]="size()"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path [attr.d]="path()" />
  </svg>`,
  styles: [':host{display:inline-flex;vertical-align:middle}'],
})
export class IconComponent {
  readonly name = input.required<string>();
  readonly size = input(18);
  protected readonly path = computed(() => PATHS[this.name()] ?? '');
}
