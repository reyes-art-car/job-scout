import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PublicShell } from '../../shared/public-shell';

interface Feature {
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
  imports: [RouterLink, PublicShell],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './landing.html',
  styleUrl: './landing.scss',
})
export class Landing {
  protected readonly steps = [
    { title: 'Sube tu CV', text: 'En PDF, DOCX o TXT. Se lee en tu navegador y el archivo no viaja a ningún servidor.' },
    { title: 'Revisa lo que ha detectado', text: 'Mira tu experiencia, tus tecnologías y tus idiomas, y corrige lo que haga falta antes de guardar.' },
    { title: 'Empieza a buscar', text: 'Puntúa ofertas contra tu perfil, adapta el CV, escribe cartas y mira qué te conviene aprender.' },
  ];

  protected readonly features: Feature[] = [
    { title: 'Panel de búsqueda', text: 'En qué punto está cada candidatura, tu compatibilidad media y las tecnologías que más se repiten en tus ofertas.' },
    { title: 'Ofertas en tabla o en Kanban', text: 'Filtra, arrastra de un estado a otro, añade ofertas a mano y exporta todo a CSV.' },
    { title: 'CV adaptado a cada oferta', text: 'Pone primero los logros y tecnologías que pide la oferta, sin inventar nada que tu CV no respalde.' },
    { title: 'Cartas de presentación', text: 'Las editas a tu gusto, en tono formal o cercano, y puedes reconocer lo que todavía estás aprendiendo.' },
    { title: 'Brecha de skills', text: 'Qué tecnologías te faltan, cuáles pesan más y qué proyecto sirve para demostrarlas.' },
    { title: 'Evidencias', text: 'Una competencia solo sube de nivel cuando la respaldas con un proyecto, un curso o un certificado.' },
  ];

  protected readonly shots: Shot[] = [
    { file: 'ofertas.png', title: 'Ofertas', text: 'Tabla filtrable y tablero Kanban, con la compatibilidad de cada una.' },
    { file: 'adaptar-cv.png', title: 'Adaptar CV', text: 'Titular, resumen y logros reordenados según la oferta.' },
    { file: 'skills.png', title: 'Brecha de skills', text: 'Lo que te falta, por prioridad, y cómo demostrarlo.' },
  ];

  protected readonly privacy = [
    'La demo y el modo local no piden cuenta ni contraseña. Solo la búsqueda automática de ofertas la necesita, y es opcional.',
    'El CV se procesa en tu navegador y no se sube a ningún servidor.',
    'Se guarda únicamente en tu dispositivo y lo borras con un clic.',
    'Sin cookies de publicidad, de analítica ni de rastreo.',
  ];
}
