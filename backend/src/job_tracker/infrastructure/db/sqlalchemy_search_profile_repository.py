import json
from dataclasses import asdict

from sqlalchemy.orm import Session

from job_tracker.domain.candidate.search_profile import SearchProfile
from job_tracker.infrastructure.db.models import SearchProfileModel


class SqlAlchemySearchProfileRepository:
    def __init__(self, session: Session):
        self._session = session

    def get(self, user_id: int) -> SearchProfile | None:
        row = self._session.get(SearchProfileModel, user_id)
        if row is None:
            return None
        try:
            return SearchProfile(**json.loads(row.data))
        except (ValueError, TypeError):
            return None  # fila corrupta: se trata como «sin perfil» y el usuario lo rehace

    def save(self, user_id: int, profile: SearchProfile) -> SearchProfile:
        data = json.dumps(asdict(profile), ensure_ascii=False)
        row = self._session.get(SearchProfileModel, user_id)
        if row is None:
            self._session.add(SearchProfileModel(user_id=user_id, data=data))
        else:
            row.data = data
        self._session.commit()
        return profile
