from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchProfile:
    """Qué busca cada usuario. Es texto libre del propio usuario: se trata como dato no confiable en el prompt."""

    headline: str  # «Desarrolladora Java junior»
    seniority: str  # «junior», «mid», «senior»…
    summary: str  # experiencia y formación en pocas líneas
    skills: list[str] = field(default_factory=list)
    target_roles: list[str] = field(default_factory=list)
    search_terms: list[str] = field(default_factory=list)
    country: str = "España"
    onsite_cities: list[str] = field(default_factory=list)  # ciudades donde acepta presencial
    accepts_hybrid: bool = True
    remote_only: bool = False
    languages: list[str] = field(default_factory=list)
    max_years_experience: int = 5
