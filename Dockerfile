FROM python:3.8-buster

ENV LANG='en_US.UTF-8'

# build-essential
RUN apt-get -qq -y update \
    && apt-get -qq -y install locales \
    ca-certificates curl jq\
    python3-pip python3-icu

WORKDIR /usr/src/app

RUN groupadd -g 1000 -r app \
    && useradd -m -u 1000 -s /bin/false -g app app

COPY requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements-dev.txt
RUN mkdir /usr/src/app/appdata
VOLUME ["/usr/src/app/appdata"]
COPY . /usr/src/app
ADD . .
RUN pip install .
CMD gunicorn --workers 2 --timeout 1200 --bind 0.0.0.0:8080 --access-logfile - wsgi:application --reload