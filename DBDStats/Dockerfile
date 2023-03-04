FROM python:3.9.16-slim-bullseye

WORKDIR /app

COPY *.py .
COPY requirements.txt .
COPY activity.json .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1

RUN python -m pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN apt-get update \
    && apt-get install -y build-essential libssl-dev libffi-dev python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt

ARG BUILD_DATE
ARG VERSION

LABEL maintainer="./𝕾𝖊𝖗𝖕𝖊𝖓𝖘𝖎𝖓.𝖘𝖍#0007"
LABEL version=$VERSION
LABEL description="Discord bot for DBD for Steam stats."
LABEL release=$BUILD_DATE

CMD ["python3", "main.py"]
