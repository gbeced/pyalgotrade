#!/bin/sh

nosetests --with-cov --cov=pyalgotrade --cov-config=coverage.cfg --cov-report=term-missing
