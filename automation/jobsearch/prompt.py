"""Construcción del prompt de búsqueda. El texto largo vive en prompts/search_prompt.txt (versionado y
revisable sin tocar código); aquí solo están las diferencias entre estrategias de búsqueda."""

import datetime
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "prompts" / "search_prompt.txt"
FRESHNESS_DAYS = 7

_RULE_6_SPAIN = (
    "6. Modalidad 100% Presencial en una ciudad distinta de Sevilla (la candidata NO "
    "puede trabajar presencialmente fuera de Sevilla). Solo son válidas: cualquier "
    "oferta remota (100% remoto, sea cual sea la ciudad), cualquier oferta híbrida en "
    "España, o presencial exclusivamente si es en Sevilla."
)
_LOCATION_SPAIN = (
    "- 10 pts: Ubicación/Modalidad (remoto 100%=10, Sevilla presencial=10, híbrido "
    "España=7). Presencial fuera de Sevilla: EXCLUIR (ver regla 6), no puntuar."
)
_TERMS_SPAIN = """- "Java junior", "Spring Boot junior", "desarrollador Java junior"
- "Angular junior", "Full Stack Java Angular junior"
- "programador Java", "backend Java junior España\""""


@dataclass(frozen=True)
class SearchStrategy:
    """Todo lo que cambia entre una búsqueda general, la de LinkedIn y la internacional."""

    label: str | None
    sources: str
    terms: str
    max_offers: int
    rule_6: str
    extra_rules: str
    location_rubric: str
    portal_field: str
    extra_note: str


STRATEGIES: dict[str, SearchStrategy] = {
    "general": SearchStrategy(
        label=None,
        sources="""- LinkedIn España (es.linkedin.com/jobs)
- Indeed España (indeed.es)
- Infojobs (infojobs.net)
- Tecnoempleo (tecnoempleo.com)
- Computrabajo España (computrabajo.es)
- Jobandtalent (jobandtalent.com)""",
        terms=_TERMS_SPAIN,
        max_offers=30,
        rule_6=_RULE_6_SPAIN,
        extra_rules="",
        location_rubric=_LOCATION_SPAIN,
        portal_field="LinkedIn/Indeed/Infojobs/Tecnoempleo/etc",
        extra_note="",
    ),
    "linkedin": SearchStrategy(
        label="LinkedIn",
        sources="""- LinkedIn España (es.linkedin.com/jobs) — ÚNICO portal a buscar en esta ejecución.
  Busca de forma exhaustiva: recorre varias páginas de resultados y varias
  combinaciones de términos, no te quedes solo con los primeros resultados.""",
        terms=_TERMS_SPAIN,
        max_offers=40,
        rule_6=_RULE_6_SPAIN,
        extra_rules="",
        location_rubric=_LOCATION_SPAIN,
        portal_field="LinkedIn/Indeed/Infojobs/Tecnoempleo/etc",
        extra_note="",
    ),
    "europa": SearchStrategy(
        label="Europa/Internacional",
        sources="""- Páginas de carreras DIRECTAS de empresas tecnológicas internacionales (no
  agregadores): busca en sus propios dominios de empleo, por ejemplo páginas
  alojadas en Lever (jobs.lever.co), Greenhouse (boards.greenhouse.io),
  Workable (jobs.workable.com / apply.workable.com), Recruitee
  (*.recruitee.com) o SmartRecruiters (careers.smartrecruiters.com) de
  empresas con sede fuera de España (Europa, Reino Unido, Latinoamérica,
  etc.).
- Bolsas de empleo remoto internacionales: Himalayas (himalayas.app),
  Jobgether (jobgether.com), WeWorkRemotely (weworkremotely.com), Working
  Nomads (workingnomads.com), Get on Board (getonbrd.com, foco Latinoamérica
  e hispanohablante), Remotive (remotive.com).""",
        terms="""- "junior java developer remote" / "junior full stack java angular remote"
- "desarrollador junior Java Angular remoto" (foco empresas Latinoamérica)
- "junior software engineer java" + "remote from Europe" / "remote worldwide\"""",
        max_offers=20,
        rule_6=(
            "6. CUALQUIER modalidad que no sea 100% remota (la candidata NO se va a reubicar "
            "a otro país, así que un puesto híbrido o presencial fuera de España queda "
            "excluido salvo que el propio puesto sea remoto desde cualquier lugar)."
        ),
        extra_rules=(
            "\n7. La empresa tiene sede en España (esta búsqueda es específicamente para "
            "empresas con sede FUERA de España; las españolas ya se cubren en la búsqueda "
            "general).\n"
            "8. El puesto exige un idioma obligatorio distinto de español o inglés (por "
            "ejemplo, alemán, francés, neerlandés o polaco nativo). El inglés fluido/C1 SÍ es "
            "válido como requisito.\n"
            "9. La oferta restringe explícitamente la residencia a un país o región "
            'incompatible con España (por ejemplo, "solo India", "solo LatAm con residencia '
            'en Chile", "solo ciudadanos de EE.UU."). Verifica esto con cuidado: muchas '
            "ofertas de consultoras de outsourcing (BairesDev, Miratech, Software Mind, etc.) "
            'anuncian "remoto mundial" pero en la descripción real solo aceptan candidatos de '
            "una región concreta que no incluye España — descártalas si detectas esa "
            "restricción."
        ),
        location_rubric=(
            "- 10 pts: Ubicación/Modalidad (100% remoto sin restricción de país=10, 100% "
            "remoto con restricción ambigua pero probablemente compatible con España=6). "
            "Cualquier cosa no remota o con restricción de país que excluya España: EXCLUIR "
            "(ver reglas 6 y 9), no puntuar."
        ),
        portal_field=(
            "Nombre de la empresa / bolsa donde se publicó "
            "(Lever, Greenhouse, Workable, Himalayas, Jobgether, Get on Board, etc.)"
        ),
        extra_note=(
            "\n- Antes de incluir una oferta, confirma explícitamente en el texto real del "
            "anuncio (no en el título de búsqueda) que un candidato residente en España puede "
            "aplicar en remoto sin reubicarse. Si la elegibilidad geográfica no está clara, "
            'indícalo en el campo "notes" en vez de asumir que es válida.'
        ),
    ),
}


def build_search_prompt(
    *,
    candidate_profile: str,
    known_urls: Iterable[str],
    last_id: int,
    today: datetime.date,
    strategy: str = "general",
) -> str:
    try:
        chosen = STRATEGIES[strategy]
    except KeyError:
        raise ValueError(f"Estrategia desconocida: {strategy!r} (válidas: {', '.join(STRATEGIES)})") from None

    cutoff = today - datetime.timedelta(days=FRESHNESS_DAYS)
    # Una URL por línea y en una sola línea: una URL con saltos de línea no puede inyectar instrucciones.
    urls = sorted({" ".join(url.split()) for url in known_urls})
    known_list = "\n".join(f"  - {url}" for url in urls) if urls else "  (ninguna aún)"

    return TEMPLATE_PATH.read_text(encoding="utf-8").format(
        today=today.strftime("%d/%m/%Y"),
        cutoff_date=cutoff.strftime("%Y-%m-%d"),
        candidate_profile=candidate_profile,
        portales_txt=chosen.sources,
        terminos_txt=chosen.terms,
        exclusion_6=chosen.rule_6,
        exclusion_extra=chosen.extra_rules,
        known_list=known_list,
        rubrica_ubicacion=chosen.location_rubric,
        next_id=f"{last_id + 1:03d}",
        portal_campo=chosen.portal_field,
        max_ofertas=chosen.max_offers,
        nota_extra=chosen.extra_note,
    )
