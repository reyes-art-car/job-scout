import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicShell } from '../../shared/public-shell';

@Component({
  selector: 'app-condiciones',
  imports: [RouterLink, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './condiciones.html',
  styleUrl: './legal.scss',
})
export class Condiciones {
  protected readonly updated = '20 de octubre de 2026';
}
