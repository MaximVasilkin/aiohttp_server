FROM python:3.10-alpine

WORKDIR /app

COPY ./app .

COPY ./requirements.txt .

EXPOSE 8080

RUN pip install -r requirements.txt

CMD gunicorn main:app --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker
