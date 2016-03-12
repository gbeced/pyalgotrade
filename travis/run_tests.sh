#!/bin/sh

export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

ls -al
nosetests --ignore-files=optimizer_testcase --with-coverage --cover-package=pyalgotrade
ls -al
