#!/bin/sh

export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

nosetests --with-coverage --cover-package=pyalgotrade
