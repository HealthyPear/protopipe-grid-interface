#!/bin/bash

# This is somewhat OP, since macos users will likely use the Docker container
# were 'realpath' is defined, but just in case...
if [[ ( "$OSTYPE" == "darwin"* ) && ( -z "$(command -v realpath)" ) ]]; then
  echo "ERROR: realpath command not found!"
  echo "You can install it with Homebrew: 'brew install coreutils'"
  return 1
fi

# Define where the source code for the interface resides
# This corresponds to where the setup.sh is located
GRID_INTERFACE_full_path=$(realpath $BASH_SOURCE)
export GRID_INTERFACE=$(dirname $GRID_INTERFACE_full_path)
echo "\$GRID_INTERFACE points to $GRID_INTERFACE"

# Check if DIRAC has been initialized
if [[ -z "${DIRAC}" ]]; then
  echo "ERROR: \$DIRAC environment variable undefined!"
  echo "Please, make sure that DIRAC has been installed and initialized."
  return 1
else
  $DIRAC/diracos/usr/bin/pip install -r "$GRID_INTERFACE/requirements.txt"
fi

# This should be also OP, but it can be that the installation has been
# done in an incorrect way and the scripts are not where they shoud be
if [ "$(command -v dirac-info)" != "$DIRAC/scripts/dirac-info" ]; then
    echo "ERROR: DIRAC scripts not accessible."
    echo "Please, make sure that DIRAC has been properly installed."
    return 1
fi
