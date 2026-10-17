# Sugerencias de evolución

Basadas en cómo has usado Claude hasta ahora para esta aplicación. Lo que se ve en el historial del proyecto:

1. **Un prompt de búsqueda muy elaborado** (`automation/busqueda_diaria.py`): rol de reclutador técnico, tres variantes (general, LinkedIn, empresas internacionales remotas), reglas de exclusión, rúbrica de 100 puntos y salida JSON con los campos del CV adaptado.
2. **Una segunda línea de búsqueda en paralelo** (docencia) y un Excel para otra persona: usas el mismo motor para más de un perfil.
3. **Unos 40 scripts `generar_cv_*` y `generar_carta_*`**, uno por oferta: pides un CV y una carta a medida cada vez que una oferta encaja.
4. **Altas manuales y limpiezas del Excel** (`agregar_ofertas_*.py`, copias de seguridad): el Excel se ha quedado corto como base de datos.
5. **Un backend a medio construir** con módulos vacíos (`llm/`, `parsing/`, `docx_generation/`), una fuente `document_upload` y cuatro modos de entrevista (`technical_question`, `behavioral_star`, `mock_interview`, `general_tips`): ya habías diseñado lo siguiente que querías.

## Propuestas, de más a menos rentables

| # | Propuesta | Por qué ahora | Esfuerzo |
|---|---|---|---|
| 1 | **Backend gemelo en Java / Spring Boot** con la misma API y los mismos tests | El tracker está en Python, pero tus ofertas piden Java. Mostrar el mismo dominio en Spring Boot 3 + JPA + Spring Security enseña al reclutador justo lo que busca | Alto |
| 2 | **Analizar una oferta pegada o subida** (`POST /api/offers/analyze`): Claude extrae los campos y la puntuación con tu rúbrica | Cierra la fuente `document_upload` ya modelada. Hoy el frontend detecta tecnologías con regex; el LLM entiende «se valora», «imprescindible» o «3 años» | Medio |
| 3 | **Generar el .docx real por oferta** en el backend (`docx_generation/`) | Sustituye los ~40 scripts por un botón y rellena `adapted_cv_filename`. Hoy el frontend descarga HTML abrible en Word | Medio |
| 4 | **Entrenador de entrevistas** con los cuatro modos ya definidos y contexto de la oferta | Prepara preguntas técnicas de Spring/Angular y STAR usando tus brechas reales; con streaming y guardado de sesiones | Medio |
| 5 | **Varios perfiles** (`profile_id` en ofertas y CVs) | Ya mantienes docencia y el Excel de otra persona. Un selector de perfil evita duplicar scripts | Medio |
| 6 | **Mejorar la rúbrica** y hacerla configurable (YAML) | El nivel solo pesa 15/100: un puesto de 5 años puntúa 82 %. Añadir un tope por experiencia, mostrar el desglose en la UI y calibrar con las ofertas que acaben en entrevista | Bajo |
| 7 | **Seguimiento de candidaturas**: fecha de envío, recordatorio a los 7 días, contacto, historial de estados | Convierte el Kanban en un CRM de búsqueda; métricas de respuesta por portal y por tramo de compatibilidad | Medio |
| 8 | **Competencia y frescura**: guardar nº de inscritos, detectar ofertas cerradas, avisar a los 30 días | Las fichas de Tecnoempleo muestran inscritos (12 frente a 3.296): es el mejor indicador de dónde aplicar | Bajo |
| 9 | **Salida estructurada en el buscador**: usar *tool use* / JSON Schema en lugar de extraer JSON con expresiones regulares | `parse_offers_json` falla si el modelo añade texto. Un esquema validado con Pydantic elimina ese fallo | Bajo |
| 10 | **Prompts versionados y probados** en `backend/knowledge_base/prompts/` con casos de referencia | Ahora el prompt vive dentro de un script de 750 líneas; separarlo permite probarlo y mejorarlo sin romper el resto | Bajo |
| 11 | **CV y carta en inglés** (conmutador de idioma) | Muchas ofertas piden «inglés alto» y la búsqueda internacional ya existe | Bajo |
| 12 | **Plan de formación con progreso** a partir de la brecha de skills | Marcar una tecnología como aprendida actualiza su nivel en el catálogo y el CV adaptado | Bajo |
| 13 | **Captura desde LinkedIn** con un *bookmarklet* que envía la oferta abierta a la API | LinkedIn bloquea la lectura automática; esto evita copiar y pegar | Bajo |
| 14 | **Alertas**: resumen diario por correo o Telegram con las ofertas nuevas ≥ 75 % | Sustituye al Programador de tareas local por una GitHub Action programada | Medio |
| 15 | **Autenticación y despliegue** (JWT + refresh, Docker Compose, VPS) | Reutiliza lo que ya dominas y deja la app online. Imprescindible antes de guardar datos personales fuera de tu equipo | Medio |

## Orden recomendado

1. **Esta semana:** 6, 8 y 9. Son pequeños y mejoran la calidad de lo que ya tienes.
2. **Este mes:** 2 y 3. Eliminan los scripts por oferta y completan la parte «Claude» de la aplicación.
3. **Después:** 1 (si quieres que el repo hable de Java), 4 y 5.
