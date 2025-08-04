FROM python:3.11.2-slim-bullseye
LABEL authors="s-storozhuk"

RUN apt-get update && apt-get upgrade -y && \
  apt-get -y install \
    libpq-dev gcc \
    pip \
    bash \
    expect \
    curl \
    git \
    htop \
    iputils-ping \
    python3-aiofiles \
    vim \
    openssl \
    libssl-dev \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache poetry==2.1.1

COPY pyproject.toml poetry.lock /app/
COPY src/ /app/src
RUN rm -rf /app/src/logs && rm -rf /app/src/static
RUN mkdir /app/src/logs && touch /app/src/logs/app.log
RUN mkdir -p /app/src/static && \
    mkdir -p /app/src/static/photos

ENV PYTHONPATH "${PYTHONPATH}:/app/src"
ENV PYTHONUNBUFFERED=TRUE

RUN cd /app && poetry config virtualenvs.create false && poetry install --no-root

WORKDIR /app/src