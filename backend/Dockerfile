FROM python:3.15.2-slim-bookworm@sha256:96599df822d0e1c6bb700014a05c7f3c8cabc6e0f7ff3c4f9f69cee033b4b5d9 AS builder
WORKDIR /build
COPY requirements.lock .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.lock

FROM python:3.15.2-slim-bookworm@sha256:96599df822d0e1c6bb700014a05c7f3c8cabc6e0f7ff3c4f9f69cee033b4b5d9
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0
RUN addgroup --system path && adduser --system --ingroup path --home /app path
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY scripts ./scripts
USER path
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"]
CMD ["python", "-m", "app.run"]
