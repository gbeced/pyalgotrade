FROM python:3.6
MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

WORKDIR /app

RUN pip install nose nose-cov matplotlib ws4py tornado

COPY . /app/
RUN pip install -U /app

CMD ./travis/run_tests.sh