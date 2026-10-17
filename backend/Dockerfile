# syntax=docker/dockerfile:1
# Imagen mínima y sin privilegios para la API. Construir desde la raíz del repositorio:
#   docker build -f backend/Dockerfile -t job-hunter-api .

FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
COPY backend/requirements.txt ./
RUN /opt/venv/bin/pip install --require-virtualenv -r requirements.txt
COPY backend/pyproject.toml ./
COPY backend/src ./src
RUN /opt/venv/bin/pip install --no-deps .

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    APP_ENV=production \
    DATABASE_URL=sqlite:////data/job_tracker.db \
    CANDIDATE_PROFILE_PATH=/app/config/candidate_profile.yaml
# Usuario sin shell ni directorio personal: si alguien compromete la API, no puede hacer casi nada.
RUN groupadd --system app \
 && useradd --system --gid app --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /data /app/config \
 && chown app:app /data
COPY --from=build /opt/venv /opt/venv
COPY backend/config/candidate_profile.example.yaml /app/config/
WORKDIR /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).status == 200 else 1)"
CMD ["uvicorn", "job_tracker.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
