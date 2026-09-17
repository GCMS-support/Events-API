FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd --create-home --uid 10001 appuser && mkdir -p /app/instance && chown appuser:appuser /app/instance
COPY --chown=appuser:appuser app.py config.py models.py openapi.yaml gunicorn.conf.py ./
COPY --chown=appuser:appuser routes ./routes

FROM base AS test
COPY requirements-dev.txt pytest.ini ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY --chown=appuser:appuser tests ./tests
USER appuser
CMD ["python", "-m", "pytest", "-q"]

FROM base AS production
ARG APP_REVISION=local
ENV APP_REVISION=$APP_REVISION
ENV PORT=5000
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','5000')+'/api/health', timeout=3)"
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
