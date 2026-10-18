FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FSIE_CHAT_ENABLE_MODEL=false
WORKDIR /app

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY packages ./packages
COPY knowledge/hong_kong/fsie/chat_corpus.json ./knowledge/hong_kong/fsie/chat_corpus.json
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home taxrora
USER taxrora

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

# Sessions are in memory: keep a single worker and a single service instance.
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
