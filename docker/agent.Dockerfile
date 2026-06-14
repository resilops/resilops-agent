FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV POETRY_VERSION=2.2.1
ENV HOME /home
ENV APP $HOME/src

RUN apt-get update && apt-get install -y procps

COPY ./src $APP
ADD ./pyproject.toml ./poetry.lock ./README.md $HOME

WORKDIR $APP

RUN pip install "poetry==${POETRY_VERSION}"
RUN poetry install --without local


# -------------------------------
# Local stage (for development)
# -------------------------------
FROM base AS local

ARG INSTALL_LOCAL=false
ARG RESILIENCE_LIB_PATH

COPY ./local-libs/resilience-lib /home/local-libs/resilience-lib

RUN poetry install --with local
