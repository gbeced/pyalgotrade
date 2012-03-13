#!/bin/sh

# Check the arguments.
if test $# -ne 1 
then
    echo 'Usage: syncdoc.sh <html path>'
    exit 1
fi


rsync -ah --progress --delete $1 .

