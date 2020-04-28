FROM gbecedillas/pyalgotrade:0.20-py27

MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

RUN apt-get update

# Remove the installed version of PyAlgoTrade since we'll be executing testcases from source.
RUN pip uninstall -y pyalgotrade

# For testcases
RUN pip install tox
RUN pip install flake8

# List installed packages
RUN pip freeze

# Files needed to execute testcases.
RUN mkdir /tmp/pyalgotrade
COPY Makefile /tmp/pyalgotrade/
COPY setup.py /tmp/pyalgotrade/
COPY travis/run_tests.sh /tmp/pyalgotrade/
COPY coverage.cfg /tmp/pyalgotrade/
COPY tox.ini /tmp/pyalgotrade/
COPY pyalgotrade /tmp/pyalgotrade/pyalgotrade
COPY testcases /tmp/pyalgotrade/testcases
COPY samples /tmp/pyalgotrade/samples

