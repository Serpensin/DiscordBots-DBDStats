FROM python:3.9.16-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY *.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1
ENV RUNNING_IN_DOCKER 'true'

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN python -m pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev; \
    fi && \
    pip install -r requirements.txt && \
    if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk del .build-deps; \
    fi && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: the_devil_of_the_rhine (863687441809801246)" \
      commit=$COMMIT \
      description="Discord bot for DBD for Steam stats." \
      release=$BUILD_DATE \
      VERSION="1.2.6" \
      url="https://gitlab.bloodygang.com/Serpensin/DBDStats"

CMD ["python3", "main.py"]
