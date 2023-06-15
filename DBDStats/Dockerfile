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

RUN python -m pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev; \
    fi
RUN pip install -r requirements.txt

LABEL maintainer="./𝕾𝖊𝖗𝖕𝖊𝖓𝖘𝖎𝖓.𝖘𝖍#0007"
LABEL commit=$COMMIT
LABEL description="Discord bot for DBD for Steam stats."
LABEL release=$BUILD_DATE
LABEL VERSION="1.2.3"
LABEL url="https://gitlab.bloodygang.com/Serpensin/DBDStats"

CMD ["python3", "main.py"]
