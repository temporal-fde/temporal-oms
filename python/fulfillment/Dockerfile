# Python worker Dockerfile for the fulfillment agents and shipping task queues.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev

COPY generated ./generated
COPY fulfillment/src ./fulfillment/src

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH="/app/generated:/app/generated/pydantic:/app/fulfillment" \
    PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "-m", "src.worker"]
