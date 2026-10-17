import datetime
from pathlib import Path

import pytest

from jobsearch.config import Paths, Profile, SkillGroup

TODAY = datetime.date(2026, 10, 17)


class FakeLlm:
    """Doble de LlmClient: devuelve una respuesta fija y guarda el prompt recibido."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


@pytest.fixture
def profile() -> Profile:
    group = [SkillGroup("Backend", "Java, Spring Boot"), SkillGroup("Frontend", "Angular")]
    return Profile(
        name="ADA LOVELACE",
        contact_line="Sevilla | ada@example.com",
        bullets=["Logro cero", "Logro uno", "Logro dos"],
        skills={"backend_first": group, "fullstack": group, "frontend_first": group},
        prompt_block="CANDIDATA: Ada",
    )


@pytest.fixture
def paths(tmp_path: Path) -> Paths:
    return Paths(
        base=tmp_path,
        cv_dir=tmp_path / "CV_adaptados",
        excel=tmp_path / "Ofertas.xlsx",
        log_dir=tmp_path / "logs",
    )


def raw_offer(**overrides: object) -> dict:
    offer: dict = {
        "id": "OF999",
        "priority": "Alta",
        "compatibility": 80,
        "title": "Junior Java Developer",
        "company": "Acme",
        "portal": "Tecnoempleo",
        "url": "https://example.com/job/1",
        "date": "2026-10-16",
        "location": "España",
        "modality": "Remoto 100%",
        "mandatory_tech": "Java, Spring Boot",
        "cv_file": "OF999_Acme_JuniorJava.docx",
        "cv_title": "JUNIOR JAVA DEVELOPER",
        "cv_summary": "Resumen adaptado",
        "cv_skills_order": "backend_first",
        "cv_bullets": [2, 0, 1],
    }
    offer.update(overrides)
    return offer
