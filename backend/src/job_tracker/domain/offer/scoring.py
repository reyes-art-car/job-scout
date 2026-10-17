from job_tracker.domain.offer.entities import Priority

# Umbral de la rúbrica de búsqueda diaria: ≥ 75 % → prioridad alta; 60-74 % → secundaria.
HIGH_PRIORITY_THRESHOLD = 75


def priority_for(compatibility: int) -> Priority:
    return Priority.ALTA if compatibility >= HIGH_PRIORITY_THRESHOLD else Priority.SECUNDARIA
