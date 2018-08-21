# ARG PYALGOTRADE_TAG
# FROM gbecedillas/pyalgotrade:${PYALGOTRADE_TAG}
FROM gbecedillas/pyalgotrade:0.20-py27

MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

RUN apt-get update

RUN pip install tox
# Required by matplotlib
RUN apt-get install -y python-tk 

RUN pip freeze

RUN mkdir /tmp/pyalgotrade

# Files needed to execute testcases.
COPY setup.py /tmp/pyalgotrade/
COPY travis/run_tests.sh /tmp/pyalgotrade/
COPY coverage.cfg /tmp/pyalgotrade/
COPY tox.ini /tmp/pyalgotrade/
COPY pyalgotrade /tmp/pyalgotrade/pyalgotrade
COPY testcases /tmp/pyalgotrade/testcases
COPY samples /tmp/pyalgotrade/samples

# Remove the installed version of PyAlgoTrade since we'll be executing testcases from source.
RUN pip uninstall -y pyalgotrade
