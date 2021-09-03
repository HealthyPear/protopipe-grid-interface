#!/bin/bash

GRID_INTERFACE_full_path=$(realpath $BASH_SOURCE)
export GRID_INTERFACE=$(dirname $GRID_INTERFACE_full_path)
echo "\$GRID_INTERFACE points to $GRID_INTERFACE"

if [[ -z "${DIRAC}" ]]; then
  echo "ERROR: DIRAC is not installed or it has not being installed properly."
  echo "\$DIRAC environment variable undefined"
  exit
else
  $DIRAC/diracos/usr/bin/pip install -r "$GRID_INTERFACE/requirements.txt"
fi

# check if dirac has been initialized
if [ "$(command -v dirac-info)" != "$DIRAC/scripts/dirac-info" ]; then
    echo "ERROR: DIRAC is not installed or it has not being installed properly."
    echo "Command 'dirac-info' could not be found or it is not where is should be..."
    exit
fi
