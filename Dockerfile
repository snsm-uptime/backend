FROM python:3.12-slim AS python-base


ENV POETRY_VIRTUALENVS_IN_PROJECT=false \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry===1.8.3

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf ${POETRY_CACHE_DIR}

COPY ./src ./src

# Copy Alembic configuration files
COPY alembic.ini alembic.ini
COPY ./migrations ./migrations

EXPOSE 80

ENTRYPOINT ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]