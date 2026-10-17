export type TechLevel = 'have' | 'partial' | 'gap';
export type TechCategory =
  | 'Backend'
  | 'Frontend'
  | 'Datos'
  | 'DevOps'
  | 'Cloud'
  | 'Mensajería'
  | 'Calidad'
  | 'Arquitectura'
  | 'IA'
  | 'Metodología'
  | 'Otros';

export interface Tech {
  id: string;
  name: string;
  category: TechCategory;
  /** have: acreditado en el CV · partial: lo usa pero no figura (o solo en proyectos) · gap: no acreditado. */
  level: TechLevel;
  /** Prioridad de aprendizaje cuando level != have (A = más repetida en ofertas). */
  priority?: 'A' | 'B' | 'C';
  /** Fuente de expresión regular (sin límites de palabra: se añaden al compilar). */
  pattern: string;
  /** Cómo cerrar la brecha con un entregable visible en GitHub. */
  plan?: string;
}

const T = (
  id: string,
  name: string,
  category: TechCategory,
  level: TechLevel,
  pattern: string,
  priority?: 'A' | 'B' | 'C',
  plan?: string,
): Tech => ({ id, name, category, level, pattern, priority, plan });

export const TECH_CATALOG: readonly Tech[] = [
  // Backend
  T('java', 'Java', 'Backend', 'have', 'java(?:\\s*(?:8|11|17|21)\\+?)?|jdk|j2se'),
  T('spring-boot', 'Spring Boot', 'Backend', 'have', 'spring\\s*boot|springboot'),
  T('spring', 'Spring Framework', 'Backend', 'have', 'spring(?!\\s*(?:boot|security|data|cloud|batch|webflux|mvc))(?:\\s*(?:framework|mvc))?|spring\\s*mvc'),
  T('spring-security', 'Spring Security', 'Backend', 'have', 'spring\\s*security'),
  T('jwt', 'JWT', 'Backend', 'have', 'jwt|json\\s*web\\s*tokens?'),
  T('rest', 'APIs REST', 'Backend', 'have', 'rest(?:ful)?(?:\\s*apis?)?|apis?\\s*rest(?:ful)?|web\\s*services?|servicios\\s*web'),
  T('jpa', 'JPA / Hibernate', 'Backend', 'have', 'jpa|hibernate|spring\\s*data|jdbc'),
  T('maven', 'Maven', 'Backend', 'have', 'maven|lombok|mapstruct'),
  T('gradle', 'Gradle', 'Backend', 'gap', 'gradle', 'C', 'Migrar el build del backend de ejemplo a Gradle (Kotlin DSL) en una rama.'),
  T('microservices', 'Microservicios', 'Arquitectura', 'gap', 'microservic(?:io|ios|es)|microservices?', 'A', 'Dividir el Job Tracker en 2 servicios con API Gateway y Docker Compose.'),
  T('spring-cloud', 'Spring Cloud', 'Backend', 'gap', 'spring\\s*cloud|eureka|resilience4j|openfeign', 'A', 'Gateway + Config Server + Discovery sobre los dos servicios.'),
  T('reactive', 'Programación reactiva (WebFlux)', 'Backend', 'gap', 'webflux|project\\s*reactor|programaci[oó]n\\s*reactiva|reactive|rxjava', 'C', 'Un endpoint WebFlux de streaming de ofertas nuevas.'),
  T('spring-batch', 'Spring Batch', 'Backend', 'gap', 'spring\\s*batch', 'C', 'Job de importación masiva del Excel de ofertas.'),
  T('grpc', 'gRPC', 'Backend', 'gap', 'grpc', 'C'),
  T('legacy-java', 'J2EE / Struts / JSF / SOAP', 'Backend', 'gap', 'j2ee|jee|java\\s*ee|struts|jsf|jsp|soap', 'C', 'Solo si apuntas a consultoras con proyectos legados.'),
  T('oauth', 'OAuth2 / OIDC / Keycloak', 'Backend', 'gap', 'oauth2?|oidc|openid(?:\\s*connect)?|keycloak', 'B', 'Delegar la autenticación del tracker en Keycloak.'),
  T('python', 'Python / FastAPI', 'Backend', 'partial', 'python|fastapi|django|flask'),
  T('node', 'Node.js', 'Backend', 'gap', 'node\\.?js|nodejs|express(?:\\.?js)?', 'B', 'Pequeña API Node con TypeScript para comparar con Spring.'),
  T('dotnet', '.NET / C#', 'Otros', 'gap', '\\.net|c#|asp\\.net', 'C'),
  T('kotlin', 'Kotlin', 'Otros', 'gap', 'kotlin', 'C'),

  // Frontend
  T('angular', 'Angular', 'Frontend', 'have', 'angular(?!\\s*js)(?:\\s*\\d+\\+?)?'),
  T('typescript', 'TypeScript', 'Frontend', 'have', 'typescript'),
  T('javascript', 'JavaScript', 'Frontend', 'have', 'javascript|ecmascript|es6'),
  T('html-css', 'HTML5 / CSS3', 'Frontend', 'have', 'html5?|css3?|sass|scss'),
  T('bootstrap', 'Bootstrap', 'Frontend', 'have', 'bootstrap|tailwind'),
  T('react', 'React / Next.js', 'Frontend', 'gap', 'react(?:\\.?js)?|reactjs|next\\.?js|redux', 'A', 'Segundo cliente del tracker en React + Vite (ya hay scaffold).'),
  T('rxjs', 'RxJS / NgRx', 'Frontend', 'gap', 'rxjs|ngrx', 'B', 'Estado del tablero Kanban con NgRx SignalStore.'),
  T('angular-material', 'Angular Material', 'Frontend', 'gap', 'angular\\s*material', 'B', 'Reescribir la tabla de ofertas con Material Table.'),
  T('vue', 'Vue.js', 'Frontend', 'gap', 'vue(?:\\.?js|3)?', 'C'),
  T('jquery', 'jQuery / AJAX', 'Frontend', 'gap', 'jquery|ajax', 'C'),

  // Datos
  T('sql', 'SQL', 'Datos', 'have', '(?:pl\\/?)?sql(?!\\s*server)|bases?\\s*de\\s*datos\\s*relacionales?|relacional(?:es)?'),
  T('mysql', 'MySQL', 'Datos', 'have', 'mysql|mariadb'),
  T('postgresql', 'PostgreSQL', 'Datos', 'have', 'postgres(?:ql)?'),
  T('oracle', 'Oracle / PL-SQL', 'Datos', 'gap', 'oracle|pl\\/?sql', 'B', 'Oracle XE en Docker y una migración del esquema del tracker.'),
  T('mongodb', 'MongoDB / NoSQL', 'Datos', 'gap', 'mongo(?:db)?|nosql|cassandra|dynamodb', 'B', 'Guardar las notas de entrevista en MongoDB.'),
  T('redis', 'Redis / caché', 'Datos', 'gap', 'redis|cach[eé]', 'C'),
  T('elastic', 'Elasticsearch / ELK', 'Datos', 'gap', 'elasticsearch|elk|kibana|logstash', 'C'),
  T('excel-csv', 'Excel / CSV', 'Datos', 'have', 'excel|csv'),

  // DevOps y cloud
  T('git', 'Git / GitHub', 'DevOps', 'have', 'git(?:hub)?|svn'),
  T('docker', 'Docker', 'DevOps', 'have', 'docker(?:[-\\s]*compose)?'),
  T('ci-cd', 'CI/CD · GitHub Actions', 'DevOps', 'have', 'ci\\s*\\/\\s*cd|ci-cd|cicd|github\\s*actions|integraci[oó]n\\s*continua|pipelines?'),
  T('jenkins', 'Jenkins', 'DevOps', 'gap', 'jenkins', 'B', 'Jenkinsfile equivalente al workflow de GitHub Actions.'),
  T('kubernetes', 'Kubernetes / Helm', 'DevOps', 'gap', 'kubernetes|k8s|helm|eks|gke', 'A', 'Minikube/kind + manifiestos y chart de Helm del tracker.'),
  T('openshift', 'OpenShift', 'DevOps', 'gap', 'openshift', 'A', 'Sandbox gratuita de Red Hat Developer + despliegue del tracker.'),
  T('sonar', 'SonarQube / calidad', 'Calidad', 'gap', 'sonar(?:qube|cloud)?|fortify|jacoco', 'B', 'SonarCloud y JaCoCo en el pipeline.'),
  T('terraform', 'Terraform / IaC', 'DevOps', 'gap', 'terraform|ansible|infrastructure\\s*as\\s*code|iac', 'C'),
  T('linux', 'Linux / Bash', 'DevOps', 'partial', 'linux|bash|shell'),
  T('aws', 'AWS', 'Cloud', 'gap', 'aws|amazon\\s*web\\s*services|ec2|ecs|s3|lambda', 'A', 'AWS Cloud Practitioner + backend en ECS/App Runner.'),
  T('azure', 'Azure', 'Cloud', 'gap', 'azure|az-?900', 'A', 'AZ-900 y despliegue en App Service.'),
  T('gcp', 'Google Cloud', 'Cloud', 'gap', 'gcp|google\\s*cloud', 'B'),
  T('cloud', 'Cloud / cloud-native', 'Cloud', 'gap', '(?<!spring\\s*)cloud(?:[-\\s]*native)?|nube', 'A'),

  // Mensajería
  T('kafka', 'Apache Kafka', 'Mensajería', 'gap', 'kafka', 'A', 'Evento «oferta nueva» producido por el buscador y consumido para generar el CV.'),
  T('mq', 'RabbitMQ / JMS / MQ', 'Mensajería', 'gap', 'rabbitmq|activemq|jms|mq\\s*series|ibm\\s*mq|apache\\s*camel|camel', 'B'),

  // Calidad y arquitectura
  T('junit', 'JUnit / Mockito', 'Calidad', 'have', 'junit|mockito|pruebas\\s*unitarias|testing|tests?\\s*unitarios?'),
  T('swagger', 'OpenAPI / Swagger', 'Calidad', 'have', 'swagger|openapi|postman|bruno'),
  T('tdd', 'TDD / BDD / Cucumber', 'Calidad', 'gap', 'tdd|bdd|cucumber|gherkin|testcontainers', 'B', 'Tests de integración con Testcontainers y un feature de Cucumber.'),
  T('solid', 'SOLID', 'Arquitectura', 'have', 'solid|clean\\s*code|patrones\\s*de\\s*dise[nñ]o|design\\s*patterns'),
  T('clean-arch', 'Arquitectura limpia / hexagonal / DDD', 'Arquitectura', 'partial', 'clean\\s*architecture|arquitectura\\s*(?:limpia|hexagonal|por\\s*capas)|hexagonal|ddd|domain[-\\s]*driven'),

  // Metodología
  T('scrum', 'Scrum / Agile', 'Metodología', 'have', 'scrum|agile|[aá]gil(?:es)?'),
  T('kanban', 'Kanban', 'Metodología', 'gap', 'kanban', 'C'),
  T('jira', 'Jira / Confluence', 'Metodología', 'gap', 'jira|confluence', 'C'),

  // IA / otros
  T('ai', 'IA aplicada / LLM', 'IA', 'partial', 'inteligencia\\s*artificial|\\bia\\b|\\bai\\b|llms?|copilot|chatgpt|claude|agentes?\\s*(?:de\\s*)?ia|sdd|spec[-\\s]*driven|genai|ia\\s*generativa'),
  T('android', 'Android (APK)', 'Frontend', 'partial', 'android|apk'),
  T('english', 'Inglés', 'Otros', 'have', 'ingl[eé]s|english'),
];

const BY_ID = new Map(TECH_CATALOG.map((t) => [t.id, t] as const));
export const techById = (id: string): Tech | undefined => BY_ID.get(id);

const COMPILED = TECH_CATALOG.map((tech) => ({
  tech,
  regex: new RegExp(`(?<![\\w+#.])(?:${tech.pattern})(?![\\w+#])`, 'i'),
}));

/** Devuelve las tecnologías del catálogo mencionadas en un texto libre. */
export function detectTechs(text: string): Tech[] {
  if (!text) return [];
  return COMPILED.filter(({ regex }) => regex.test(text)).map(({ tech }) => tech);
}

export const LEVEL_WEIGHT: Record<TechLevel, number> = { have: 1, partial: 0.5, gap: 0 };
