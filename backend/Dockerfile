FROM python:3.8.5-slim

LABEL author="andyi95"
LABEL maintainer="Andrey Chernikov"
LABEL release-date="2021-08-18"

WORKDIR /code

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r /code/requirements.txt

COPY . /code

CMD gunicorn foodgram_api.wsgi:application --bind 0.0.0.0:8000
