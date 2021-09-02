#!/bin/bash

export PATH=$PATH:./

echo $@ | awk 'BEGIN{RS="&&"}{print}' | while read CMD
do
    $CMD
    if [[ ( $? != 0 ) ]]; then
      echo "Error while executing $CMD"
      exit -1
    fi
done
