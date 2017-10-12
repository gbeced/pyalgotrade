FROM python:3.6
MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

RUN pip install nose nose-cov matplotlib

WORKDIR /app

COPY . /app/

RUN pip install -U /app

CMD ./travis/run_tests.sh