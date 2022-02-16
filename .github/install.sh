#!/bin/bash

if [[ "$INSTALL_METHOD" == "conda" ]]; then
  echo "Using conda"
  sudo chown -R "$USER" "$CONDA" # Give CONDA permission to its own files
  source "$CONDA"/etc/profile.d/conda.sh
  conda config --set always_yes yes --set changeps1 no
  conda update -q conda  # get latest conda version
  # Useful for debugging any issues with conda
  conda info -a

  sed -i -e "s/- python=.*/- python=$PYTHON_VERSION/g" environment_development.yaml
  conda install -c conda-forge mamba
  mamba env create -n CI --file environment_development.yaml
  conda activate CI
else
  echo "Using pip"
  pip install -U pip setuptools wheel
  # This installation is not currently supported
fi