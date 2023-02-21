FROM python:3.9.16-slim-bullseye

WORKDIR /app

COPY main.py .
COPY requirements.txt .
COPY activity.json .

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
