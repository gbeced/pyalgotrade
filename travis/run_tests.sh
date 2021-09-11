#!/bin/sh

export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
# This is needed to avoid "Coverage.py warning: No data was collected" from cov plugin.
export PYTHONPATH=.

tox -v -e py37
