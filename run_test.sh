#!/bin/sh

list=`find ./testcases -name "*test.py"`
exclude_files="./testcases/twitter_test.py ./testcases/quandl_test.py ./testcases/bitstamp_test.py ./testcases/pusher_test.py"
testlog="unittest.log"

`rm -f $testlog`
for file in $list
do
    if [[ $exclude_files =~  $file ]]
    then
        continue
    fi
    cmd="python -m unittest $file"
    echo $cmd >> $testlog
    `$cmd >> $testlog 2>&1`
done
