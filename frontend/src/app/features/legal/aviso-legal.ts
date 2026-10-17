import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicShell } from '../../shared/public-shell';

@Component({
  selector: 'app-aviso-legal',
  imports: [RouterLink, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './aviso-legal.html',
  styleUrl: './legal.scss',
})
export class AvisoLegal {
  protected readonly updated = '17 de octubre de 2026';
}
