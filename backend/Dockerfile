FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install --reinstall libpq-dev -y
RUN apt update && apt install postgresql gcc -y

COPY requirements.txt .

RUN python -m pip install --upgrade pip && pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000"]