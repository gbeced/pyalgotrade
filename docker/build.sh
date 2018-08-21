#!/bin/bash

# Build and tag Python 2.7 images
docker build --build-arg PYTHON_VERSION=2.7 -t pyalgotrade:0.20 .
docker tag pyalgotrade:0.20 pyalgotrade:0.20-py27
docker tag pyalgotrade:0.20 gbecedillas/pyalgotrade:0.20
docker tag pyalgotrade:0.20-py27 gbecedillas/pyalgotrade:0.20-py27

# Build and tag Python 3.7 images
docker build --build-arg PYTHON_VERSION=3.7 -t pyalgotrade:0.20-py37 .
docker tag pyalgotrade:0.20-py37 gbecedillas/pyalgotrade:0.20-py37

# Push images
docker login --username=gbecedillas
# docker push gbecedillas/pyalgotrade:0.20
docker push gbecedillas/pyalgotrade:0.20-py27
docker push gbecedillas/pyalgotrade:0.20-py37

# docker rmi $(docker images --quiet --filter "dangling=true")
