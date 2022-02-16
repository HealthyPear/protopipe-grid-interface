#!/bin/bash

export PATH=$PATH:./

echo $@ | awk 'BEGIN{RS="&&"}{print}' | while read CMD
do
    $CMD
    export status=$?
    if [[ ( $status != 0 ) ]]; then
      echo "Error while executing $CMD ==========> ERROR CODE: $status"
      exit $status
    fi
done
