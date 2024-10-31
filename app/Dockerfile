FROM python:3.12-alpine

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN ls -la /app

RUN poetry install --no-root --no-dev

COPY . .

ENTRYPOINT ["poetry", "run"]

CMD ["run-api"]
