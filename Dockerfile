FROM python:3.12

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update && \
    apt install --no-install-recommends -y build-essential locales-all wait-for-it && \
    python -m pip --no-cache-dir install --upgrade pip
RUN python -m pip install poetry && poetry config virtualenvs.create false

WORKDIR /server
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --only main
COPY .env manage.py ./
