FROM python:3.12-slim-bullseye
LABEL authors="shiro-kreishi"

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 80

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./src /usr/src/app