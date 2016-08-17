#!/bin/bash

docker build -t pyalgotrade:0.18 .
# docker rmi $(docker images --quiet --filter "dangling=true")

# docker tag -f pyalgotrade:0.18 gbecedillas/pyalgotrade:0.18
# docker login --username=gbecedillas --email=gbecedillas@gmail.com
# docker push gbecedillas/pyalgotrade:0.18

