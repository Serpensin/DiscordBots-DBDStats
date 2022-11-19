FROM python:3.9.15-slim-bullseye

WORKDIR /app

COPY DBDStats.py .
COPY requirements.txt .
COPY activity.json .

RUN pip install -r requirements.txt

CMD ["python3", "DBDStats.py"]
