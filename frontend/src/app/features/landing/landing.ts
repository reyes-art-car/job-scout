import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { IconComponent } from '../../shared/icon.component';
import { PublicShell } from '../../shared/public-shell';

interface Feature {
  icon: string;
  title: string;
  text: string;
}

interface Shot {
  file: string;
  title: string;
  text: string;
}

@Component({
  selector: 'app-landing',
  imports: [RouterLink, IconComponent, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './landing.html',
  styleUrl: './landing.scss',
})
export class Landing {
  protected readonly steps = [
    { title: 'Sube tu CV', text: 'PDF, DOCX o TXT. Se lee en tu navegador; el archivo no se envía a ningún servidor.' },
    { title: 'Revisa lo detectado', text: 'Comprueba tu experiencia, tus tecnologías y tus idiomas, y corrige lo que haga falta antes de guardar.' },
    { title: 'Trabaja tu búsqueda', text: 'Puntúa ofertas contra tu perfil, adapta el CV, genera cartas y descubre qué te falta aprender.' },
  ];

  protected readonly features: Feature[] = [
    { icon: 'grid', title: 'Panel de búsqueda', text: 'Embudo de candidaturas, compatibilidad media y las tecnologías más pedidas en tus ofertas.' },
    { icon: 'briefcase', title: 'Ofertas en tabla y Kanban', text: 'Filtra, arrastra entre estados, añade ofertas a mano con compatibilidad estimada y exporta a CSV.' },
    { icon: 'file', title: 'CV adaptado a cada oferta', text: 'Prioriza tus logros y tecnologías según la oferta, sin inventar experiencia que tu CV no respalda.' },
    { icon: 'mail', title: 'Cartas de presentación', text: 'Cartas editables en tono formal o cercano, con la opción de reconocer lo que aún estás aprendiendo.' },
    { icon: 'target', title: 'Brecha de skills', text: 'Qué tecnologías te faltan, cuáles pesan más y qué proyecto puede demostrarlas.' },
    { icon: 'check', title: 'Evidencias, no promesas', text: 'Una competencia sube de nivel solo cuando la respaldas con un proyecto, curso o certificado.' },
  ];

  protected readonly shots: Shot[] = [
    { file: 'ofertas.png', title: 'Ofertas', text: 'Tabla filtrable y tablero Kanban con la compatibilidad de cada oferta.' },
    { file: 'adaptar-cv.png', title: 'Adaptar CV', text: 'Titular, resumen y logros ordenados según lo que pide la oferta.' },
    { file: 'skills.png', title: 'Brecha de skills', text: 'Qué te falta, por prioridad y con un plan para demostrarlo.' },
  ];

  protected readonly privacy = [
    'Sin cuentas ni contraseñas.',
    'Tu CV se procesa en tu navegador y no se sube a ningún servidor.',
    'Solo se guarda en tu dispositivo (almacenamiento local), y puedes borrarlo con un clic.',
    'Sin cookies de publicidad, analítica ni rastreo de terceros.',
  ];
}
