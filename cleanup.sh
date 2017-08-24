#!/bin/sh

find . -name *.pyc -delete
find . -name .coverage -delete
find . -name .noseids -delete
find . -name htmlcov -exec rm -rf {} \;
