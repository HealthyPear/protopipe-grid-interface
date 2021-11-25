#!/bin/bash

# This is somewhat OP, since macos users will likely use the Docker container
# were 'realpath' is defined, but just in case...
if [[ ( "$OSTYPE" == "darwin"* ) && ( -z "$(command -v realpath)" ) ]]; then
  echo "ERROR: realpath command not found!"
  echo "Please,"
  echo " - either use the Docker Container,"
  echo " - or install the command using Homebrew (brew install coreutils)."
  return 1
fi

# Define where the source code for the interface resides
# This corresponds to where the setup.sh is located
GRID_INTERFACE_full_path=$(realpath $BASH_SOURCE)
export GRID_INTERFACE=$(dirname $GRID_INTERFACE_full_path)
echo "\$GRID_INTERFACE points to $GRID_INTERFACE"

# Define where the source code of protopipe is stored
# Same folder as the interface (as per installation instructions)
export PROTOPIPE="$(dirname $GRID_INTERFACE)/protopipe"
echo "\$PROTOPIPE points to $PROTOPIPE"

# Set VOMS
export X509_CERT_DIR=$CONDA_PREFIX/etc/grid-security/certificates
export X509_VOMS_DIR=$CONDA_PREFIX/etc/grid-security/vomsdir
export X509_VOMSES=$CONDA_PREFIX/etc/grid-security/vomses

# Check that dirac scripts are accessible
dirac_configure_command_path=$(command -v dirac-configure)

if [ ! $dirac_configure_command_path &> /dev/null ]; then
  echo "dirac-configure could not be found"
  echo "DIRAC scripts not accessible."
  return 1
else
  dirac-configure
fi

echo "The protopipe GRID interface is ready to be used!"
