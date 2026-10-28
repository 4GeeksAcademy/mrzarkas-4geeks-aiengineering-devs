FROM python:3.12-slim AS base

RUN pip install --no-cache-dir uv==0.8.22

WORKDIR /app

COPY pyproject.toml uv.lock requirements.txt ./
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

FROM base AS production

# Install the project itself so [project.scripts] creates seed-catalogs.
RUN uv export --frozen --no-dev --no-emit-project --output-file /tmp/requirements.txt --quiet \
    && cmp requirements.txt /tmp/requirements.txt \
    && uv venv \
    && uv pip install -r requirements.txt \
    && uv sync --frozen --no-dev

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS test

COPY tests ./tests
RUN uv sync --frozen

CMD ["uv", "run", "--no-sync", "pytest", "-q"]
