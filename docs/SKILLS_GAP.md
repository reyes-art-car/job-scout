# Brecha tecnológica · qué falta para un CV completo

Segundo análisis, **independiente de la búsqueda de ofertas**, hecho para medir qué tecnologías piden hoy las ofertas de tu perfil y cuáles no figuran en tu currículum.

**Fuentes cruzadas (17/10/2026):**

1. Tu tracker: 49 ofertas activas en `Ofertas_Maria_Reyes.xlsx` (columnas *Tecnologías obligatorias / deseables / Requisitos que NO cumplo*).
2. Foto del mercado hoy en Tecnoempleo: 30 ofertas por listado en Java, Spring Boot, Angular, Fullstack y Junior, más 14 fichas leídas completas.
3. Mención en listados de LinkedIn e InfoJobs (sólo títulos y etiquetas).

> Las cifras son **frecuencias de aparición en una muestra**, no estadísticas del mercado. Sirven para ordenar prioridades, no para citarlas.

## 1. Lo que ya tienes y el mercado confirma

Java (36/49 ofertas), Spring Boot (34), PostgreSQL (19), Angular (18), APIs REST (11), Git (14), Docker (8), CI/CD (11), JPA/Hibernate, Maven, JUnit/Mockito, Scrum, Spring Security. Sin huecos aquí: tu base es la que más se pide.

## 2. Lo que falta, por prioridad

### Prioridad A · aparece en muchas ofertas y cierra candidaturas

| # | Tecnología | Evidencia | Por qué importa | Cómo acreditarla rápido |
|---|---|---|---|---|
| 1 | **Microservicios + Spring Cloud** (Gateway, Eureka/Discovery, Config, OpenFeign, Resilience4j) | Obligatoria en **18/49** ofertas del tracker; en ~8 de 30 del listado Java de hoy | Es el requisito más repetido que no aparece en tu CV | Dividir el backend del *Job Tracker* en 2 servicios con Gateway y desplegarlos con Docker Compose |
| 2 | **Apache Kafka / mensajería** (eventos, productores y consumidores) | Obligatoria 4, deseable 5 en el tracker; 5+ ofertas del listado Java de hoy (Second Window, CAS, CMV, PANEL, Arelance) | Aparece en cuanto la oferta sube de junior a semi-senior | Publicar un evento «oferta nueva» desde el scraper y consumirlo para generar el CV adaptado |
| 3 | **React** (+ TypeScript, hooks, estado) y **Next.js** | Deseable en 8 y obligatoria en 3 del tracker; **12 de 30** ofertas Fullstack de hoy; hay 5+ ofertas «Java + React» frescas (Baoss, CAS, Arelance, Grupo NS) | Es el segundo frontend del mercado y casi el único que se pide junto a Java si no es Angular | Una versión del frontend del tracker en React (ya tienes el scaffold Vite) |
| 4 | **Cloud: AWS** (EC2, S3, RDS, ECS/EKS, IAM) y **Azure** | AWS deseable en 8, Azure en 6; frecuente en ofertas de Deloitte, UST, Talan, Capgemini | Aparece como «plus» en casi todo; certificarlo destaca en juniors | Certificación **AWS Cloud Practitioner** o **AZ-900**; desplegar el backend en ECS/App Service |
| 5 | **Kubernetes y OpenShift** (+ Helm) | Kubernetes deseable en 6; **OpenShift obligatoria en 6** (y la causa más repetida de «no acreditado») | Ya dominas Docker: es el siguiente peldaño natural | Minikube/kind local + manifiestos del tracker; documentar en `docs/` |

### Prioridad B · aparece con frecuencia media

| # | Tecnología | Evidencia | Acción |
|---|---|---|---|
| 6 | **Bases de datos: Oracle / PL-SQL y NoSQL (MongoDB)** | Oracle obligatoria 5, MongoDB obligatoria 6 | Una colección MongoDB para notas de entrevistas; practicar PL/SQL con Oracle XE |
| 7 | **Jenkins** y calidad de código (**SonarQube**, JaCoCo) | Jenkins obligatoria 4; SonarQube mencionada en varias | Ya usas GitHub Actions: añadir Sonar al pipeline y un `Jenkinsfile` equivalente |
| 8 | **Testing avanzado**: TDD/BDD (Cucumber), Testcontainers, tests E2E | TDD/BDD pedidos por Merkle; JUnit/Mockito ya cubiertos | Tests de integración con Testcontainers en el backend |
| 9 | **OAuth2 / OIDC / Keycloak** | Deseable en Arelance y otras ofertas de seguridad | Evolución natural de tu JWT + RBAC: delegar la autenticación en Keycloak |
| 10 | **Java 17/21 y Spring Boot 3.x** | Serem pide Java 17/21 y Spring Boot 3; JobRise lo marca como estándar 2026 | Nombrar la versión exacta en el CV (records, sealed classes, virtual threads) |
| 11 | **Angular avanzado**: RxJS, NgRx, Angular Material, signals, tests (Jasmine/Jest) | RxJS en 3 ofertas obligatorias; Material en SlashMobility y Aubay | El nuevo frontend del tracker usa signals y componentes *standalone* |
| 12 | **Arquitectura limpia / hexagonal / DDD** | Deseable en 3 del tracker; obligatoria en Serem | **Ya la aplicas** en el backend del tracker: añadirlo al CV con enlace al repo |

### Prioridad C · valor diferencial para perfiles junior

| # | Tecnología | Evidencia | Acción |
|---|---|---|---|
| 13 | **IA aplicada al desarrollo**: LLM APIs, agentes, desarrollo guiado por especificaciones (SDD), Copilot/Claude Code | knowmad mood (SDD), Arelance (LLMs y agentes), Grupo Digital («AI Native»), Logicalis (AI Engineer Junior), Social You | **Ya lo haces** (el tracker usa la API de Claude). Añadir una línea clara al CV |
| 14 | **Spring WebFlux / Project Reactor, Spring Batch, gRPC** | WebFlux en 2 ofertas, Batch y gRPC en listados de hoy | Sólo si la oferta lo pide; curso corto |
| 15 | **Python / FastAPI** | Deseable en Arelance y en varias ofertas de datos/IA; en el tracker aparece como «no acreditado» | **Ya lo usas** en el backend del tracker; falta nombrarlo en el CV |
| 16 | **Jira, Confluence, Kanban, GitFlow** | Kanban 3 obligatorias; Jira/Confluence en roles de análisis | Mencionar en el CV las metodologías que ya aplicas |
| 17 | **SOAP / J2EE / Struts / JSF** (legado) | Struts 2, J2EE 3, JSF 1 | Baja prioridad. Sólo aprender lo mínimo si apuntas a consultoras tipo Seltime |

## 3. Cosas que ya sabes pero no aparecen en el CV

Revisa que figuren explícitamente (cada una cubre al menos una oferta del listado de hoy):

- **Python y FastAPI**, **SQLAlchemy**, **Alembic** (backend del tracker).
- **Arquitectura hexagonal / clean architecture** (capas `domain`, `application`, `infrastructure`).
- **Integración con LLM** (API de Anthropic) y automatización con scripts.
- **OpenAPI/Swagger** y pruebas con **Bruno/Postman**.
- **Versiones** exactas: Java, Spring Boot 3.x, Angular 20+, TypeScript.
- **Inglés C1** debe estar arriba: lo piden Arelance, CAS, Merkle e Indra.

## 4. Plan de 8 semanas (propuesta)

| Semanas | Objetivo | Entregable |
|---|---|---|
| 1–2 | Frontend React del tracker + Next.js básico | Segunda versión del cliente en el repo |
| 3–4 | Microservicios con Spring Cloud + Docker Compose | Servicio de ofertas + servicio de CVs |
| 5 | Kafka (eventos de ofertas nuevas) | Productor y consumidor funcionando |
| 6 | Kubernetes local + Helm | Manifiestos y guía en `docs/` |
| 7–8 | AWS Cloud Practitioner + despliegue | Certificación + backend desplegado |

Cada hito se acredita con un commit visible en GitHub: ese es el argumento para el reclutador.
