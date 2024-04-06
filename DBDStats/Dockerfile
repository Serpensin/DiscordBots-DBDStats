FROM python:3.12.2-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY main.py .
COPY __init__.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1
ENV RUNNING_IN_DOCKER 'true'

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

# Install build dependencies and curl
RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libc-dev linux-headers rust cargo g++ && \
    apk add --no-cache curl && \
    python -m pip install --upgrade pip && \
    pip install --upgrade setuptools wheel && \
    pip install -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local \( -type d -a -name test -o -name tests \) -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip


EXPOSE 5000

LABEL MAINTAINER="Discord: the_devil_of_the_rhine (863687441809801246)" \
      COMMIT=$COMMIT \
      DESCRIPTION="Discord bot for DBD for Steam stats." \
      RELEASE=$BUILD_DATE \
      VERSION="1.11.0" \
      URL="https://gitlab.bloodygang.com/Serpensin/DBDStats"

CMD ["python3", "main.py"]