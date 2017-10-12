FROM gbecedillas/pyalgotrade:latest
MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

RUN python3.6 -m pip install nose
RUN python3.6 -m pip install nose-cov

RUN mkdir /tmp/pyalgotrade

# Files needed to execute testcases.
COPY travis/run_tests.sh /tmp/pyalgotrade/
COPY coverage.cfg /tmp/pyalgotrade/
COPY setup.cfg /tmp/pyalgotrade/
COPY testcases /tmp/pyalgotrade/testcases
COPY samples /tmp/pyalgotrade/samples

# We need to upgrade the installed version with the one checked out from GIT.
COPY setup.py /tmp/pyalgotrade/
COPY pyalgotrade /tmp/pyalgotrade/pyalgotrade
RUN python3.6 -m pip install -U /tmp/pyalgotrade
