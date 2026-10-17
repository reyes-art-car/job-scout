from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SkillGroup:
    label: str
    content: str


@dataclass(frozen=True)
class CandidateProfile:
    name: str
    title: str
    location: str
    phone: str
    email: str
    contact_line: str
    summary_prompt_block: str
    bullets: list[str]
    skills: dict[str, list[SkillGroup]]
    education: str
    languages: str


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache
def load_candidate_profile(path: Path) -> CandidateProfile:
    data = _load_yaml(path)
    skills = {
        order_name: [SkillGroup(**group) for group in groups]
        for order_name, groups in data["skills"].items()
    }
    return CandidateProfile(
        name=data["name"],
        title=data["title"],
        location=data["location"],
        phone=data["phone"],
        email=data["email"],
        contact_line=data["contact_line"],
        summary_prompt_block=data["summary_prompt_block"],
        bullets=data["bullets"],
        skills=skills,
        education=data["education"],
        languages=data["languages"],
    )
