# Precios y costes de IA

Estimación para decidir los planes de Job Hopping & Learning. Los tokens por acción son **estimaciones mías**,
no mediciones: hay que contrastarlas con `usage` de las respuestas reales en cuanto exista la primera
funcionalidad con LLM.

## Precio de los modelos (por millón de tokens, API de Anthropic)

| Modelo | Entrada | Salida | Lectura de caché | Batch |
| --- | --- | --- | --- | --- |
| Haiku 5.5 (`claude-haiku-5-5`) | $0,10 | $0,50 | ≈ 10 % de la entrada | −50 % |
| Sonnet 5.5 (`claude-sonnet-5-5`) | $2 | $10 | $0,20 | −50 % |
| Opus 5.5 (`claude-opus-5-5`) | $4 | $20 | $0,20 | −50 % |
| Fable 5.1 (`claude-fable-5-1`) | $10 | $50 | $0,25 | −50 % |

Haiku 5.5 sube a $0,50 / $2,50 si el prompt supera 100K tokens. La escritura de caché se factura por encima de la
entrada normal; no la he incluido (el prefijo de rúbrica se escribe una vez y se lee muchas). Los precios son los
de la tabla cacheada el 2026-10-06: revísalos antes de fijar tarifas.

## Coste por acción (con caché del prompt de sistema y la rúbrica)

| Acción | Modelo | Tokens (entrada / salida) | Coste |
| --- | --- | --- | --- |
| Analizar oferta y puntuar | Haiku 5.5 | 6.500 / 1.200 | $0,001 |
| Analizar oferta y puntuar | Sonnet 5.5 | 6.500 / 1.200 | $0,020 |
| Adaptar CV a una oferta | Sonnet 5.5 | 7.000 / 1.500 | $0,024 |
| Carta de presentación | Sonnet 5.5 | 5.000 / 700 | $0,012 |
| Turno de entrenador de entrevistas | Sonnet 5.5 | 5.000 / 600 | $0,011 |
| Búsqueda diaria de ofertas (sin coste de la herramienta de búsqueda web) | Sonnet 5.5 | 30.000 / 4.000 | $0,095 |

Con batch (trabajos no urgentes, p. ej. el resumen nocturno) todo cuesta la mitad. Recomendación: **Haiku 5.5 para
extraer y puntuar ofertas, Sonnet 5.5 para redactar CV, cartas y entrevistas**. Opus solo si una prueba muestra
que Sonnet no llega en calidad (una carta con Opus cuesta ≈ $0,023, el doble).

## Planes propuestos (precios con IVA incluido)

| | Gratis | Sprint 7 días | Pro | Plus |
| --- | --- | --- | --- | --- |
| Precio | 0 € | 5 € (pago único) | 9 €/mes | 19 €/mes |
| Análisis de ofertas | 5/mes (Haiku) | 25 | 40/mes | 100/mes |
| CV adaptados | – | 10 | 20/mes | 40/mes |
| Cartas | – | 10 | 20/mes | 40/mes |
| Turnos de entrevista | – | 20 | 30/mes | 100/mes |
| Búsquedas diarias | – | – | – | 15/mes |
| Coste IA estimado | $0,005 | $1,05 | $1,81 | $5,85 |
| Margen tras IVA 21 % y pasarela | −$0,005 | ≈ 72 % | ≈ 74 % | ≈ 61 % |

Margen = (precio − IVA − comisión de pago aprox. 1,5 % + 0,25 €) − coste IA, tratando $ y € como iguales
(prudente). No incluye hosting, correo, impuestos de sociedades ni tu tiempo.

## Cómo proteger el margen

- **Cuotas duras por plan** y límite por minuto en el backend; sin cuota, la acción no llama al modelo.
- **`max_tokens` acotado** en cada llamada y caché del prompt de sistema (ya es el 45 % de la entrada).
- **Tope mensual de gasto** en la consola de Anthropic y alerta al 80 %.
- Un usuario que gasta 3× la cuota Pro cuesta ≈ $5,4: sigue sin dar pérdidas con Pro a 9 €, pero hay que medirlo.
- Verifica antes de lanzar: términos de uso de Anthropic para reventa de funciones basadas en la API, RGPD (el CV es
  dato personal; ya hay textos legales en el frontend) y alta como autónoma para facturar.
