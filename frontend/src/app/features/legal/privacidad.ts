import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicShell } from '../../shared/public-shell';

@Component({
  selector: 'app-privacidad',
  imports: [RouterLink, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './privacidad.html',
  styleUrl: './legal.scss',
})
export class Privacidad {
  protected readonly updated = '17 de octubre de 2026';
}
