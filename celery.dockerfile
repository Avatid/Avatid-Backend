FROM python:3.11
LABEL MAINTAINER="Pixelfield, s.r.o"

ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get -y dist-upgrade
RUN apt install -y netcat-traditional
RUN apt install -y libgdal-dev


COPY ./requirements.txt /requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r /requirements.txt
RUN pip3 install psycopg2-binary

RUN apt install gettext -y

RUN mkdir /app
WORKDIR /app
COPY ./app /app
COPY ./scripts /scripts

CMD ["sh", "/scripts/celery_run.sh"]