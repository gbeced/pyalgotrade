FROM gbecedillas/pyalgotrade:0.17
MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

RUN pip install nose
RUN pip install coveralls

RUN mkdir /tmp/testcases
COPY travis/run_tests.sh /tmp/testcases
COPY coverage.cfg /tmp/testcases
COPY setup.cfg /tmp/testcases
COPY testcases /tmp/testcases/
COPY samples /tmp/testcases/

