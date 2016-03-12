#!/bin/bash

docker build -t pyalgotrade:0.17 .
# docker rmi $(docker images --quiet --filter "dangling=true")

# docker tag pyalgotrade:0.17 gbecedillas/pyalgotrade:0.17
# docker login --username=gbecedillas --email=gbecedillas@gmail.com
# docker push gbecedillas/pyalgotrade:0.17

