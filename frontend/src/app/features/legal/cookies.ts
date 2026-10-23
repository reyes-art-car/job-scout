import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicShell } from '../../shared/public-shell';

interface StorageItem {
  key: string;
  type: string;
  purpose: string;
  lifetime: string;
}

@Component({
  selector: 'app-cookies',
  imports: [RouterLink, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './cookies.html',
  styleUrl: './legal.scss',
})
export class Cookies {
  protected readonly updated = '20 de octubre de 2026';

  protected readonly items: StorageItem[] = [
    {
      key: 'jobhunter.profile.v1',
      type: 'Almacenamiento local',
      purpose: 'Guarda el perfil que confirmas a partir de tu CV.',
      lifetime: 'Hasta que lo borres',
    },
    {
      key: 'jobhunter.demo.offers.v1',
      type: 'Almacenamiento local',
      purpose: 'Guarda tus ofertas, su estado y tus notas.',
      lifetime: 'Hasta que lo borres',
    },
    {
      key: 'jobscout.career.v1',
      type: 'Almacenamiento local',
      purpose: 'Guarda tus evidencias, el progreso de tus competencias y las versiones de CV.',
      lifetime: 'Hasta que lo borres',
    },
    {
      key: 'jobhunter.api.token',
      type: 'Almacenamiento de sesión',
      purpose: 'Token de sesión que se guarda al iniciar sesión con tu cuenta (opcional). Se envía solo a la API de este sitio.',
      lifetime: 'Hasta cerrar sesión o la pestaña',
    },
  ];
}
