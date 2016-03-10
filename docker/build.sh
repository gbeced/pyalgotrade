#!/bin/bash

docker build -t pyalgotrade:0.17 .
# docker rmi $(docker images --quiet --filter "dangling=true")
