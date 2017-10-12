FROM ubuntu:latest
MAINTAINER Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y -qq install python-software-properties
RUN DEBIAN_FRONTEND=noninteractive apt-get -y -qq install software-properties-common
RUN DEBIAN_FRONTEND=noninteractive add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update

RUN apt-get -y -qq install \
	build-essential python-setuptools python-dev python-pip \
	gfortran libopenblas-dev liblapack-dev \
	pkg-config wget \
	python3.6 python3-setuptools python3.6-dev python3-pip python3.6-venv \
	libfreetype6-dev libxft-dev blt-dev python3-matplotlib


# TA-Lib
RUN cd /tmp; \
	wget http://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz; \
	tar -xzf ta-lib-0.4.0-src.tar.gz; \
	cd /tmp/ta-lib; \
	./configure ; make; make install; \
	cd /tmp/; \
	rm ta-lib-0.4.0-src.tar.gz; \
	rm -rf ta-lib


# Install the python depencencies
RUN python3.6 -m pip install pip --upgrade
RUN python3.6 -m pip install wheel

# Install our python package for running pyalgotrade
RUN python3.6 -m pip install \
	numpy scipy pandas patsy statsmodels \
	matplotlib ws4py \
	tornado tweepy cython \
	TA-Lib

RUN python3.6 -m pip install pyalgotrade==0.18
