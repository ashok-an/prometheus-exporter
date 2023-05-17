FROM python:3.10-slim-buster

WORKDIR /app

COPY metrics.py metrics.py
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

EXPOSE 8000 

CMD ["python", "metrics.py"]

