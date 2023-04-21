FROM python:3.10-alpine

WORKDIR /app

COPY ./app .

EXPOSE 8080

CMD pip install -r requirements.txt && \
    python3 work_with_db.py && \
    python3 main.py
