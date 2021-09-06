#!/bin/bash

GRID_INTERFACE_full_path=$(realpath $BASH_SOURCE)
export GRID_INTERFACE=$(dirname $GRID_INTERFACE_full_path)
echo "\$GRID_INTERFACE points to $GRID_INTERFACE"

if [[ -z "${DIRAC}" ]]; then
  echo "ERROR: \$DIRAC environment variable undefined!"
  echo "Please, make sure that DIRAC has been installed and initialized."
else
  $DIRAC/diracos/usr/bin/pip install -r "$GRID_INTERFACE/requirements.txt"
fi

# check if dirac has been initialized
if [ "$(command -v dirac-info)" != "$DIRAC/scripts/dirac-info" ]; then
    echo "ERROR: DIRAC scripts not accessible."
    echo "Please, make sure that DIRAC has been properly installed."
fi
