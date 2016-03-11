#!/bin/sh

export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

nosetests --ignore-files=optimizer_testcase --with-coverage --cover-package=pyalgotrade
