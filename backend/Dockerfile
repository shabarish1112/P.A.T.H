FROM python:3.15.0-slim-bookworm@sha256:0e019bbdfb5d9874cb2389f1c2884b64aa2ac97c99960b5bc521cef978c0617d AS builder
WORKDIR /build
COPY requirements.lock .
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.lock

FROM python:3.15.0-slim-bookworm@sha256:0e019bbdfb5d9874cb2389f1c2884b64aa2ac97c99960b5bc521cef978c0617d
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
