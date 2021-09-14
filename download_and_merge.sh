#!/usr/bin/env bash

# ============================================
#           EDIT ONLY THIS PART
# ============================================

# ANALYSIS STEP DATA TYPE
# Possible choices are,
# - TRAINING/for_energy_estimation
# - TRAINING/for_particle_classification
# - DL2
DATA_TYPE=""

PARTICLE=""  # This can be list up to "gamma proton electron"

# ============================================
#           DO NOT EDIT THIS PART
# ============================================

MODE="tail"  # also "wave" (wavelet) cleaning, but disabled for the moment

# GRID environment variables
HOME_PATH_GRID=""
ANALYSIS_PATH_GRID=""

# ANALYSIS environment variables
LOCAL=""
ANALYSIS_NAME=""
ANALYSIS_PATH_LOCAL="$LOCAL/shared_folder/analyses/$ANALYSIS_NAME"

# DIRAC file catalog full path
INPUT_DIR="$HOME_PATH_GRID/$ANALYSIS_PATH_GRID/$ANALYSIS_NAME/data/$DATA_TYPE"
# Full path in local virtual environment for the grid interface
OUTPUT_DIR="$ANALYSIS_PATH_LOCAL/data/$DATA_TYPE"

# FILE TYPE
case $DATA_PATH in
  "TRAINING/for_energy_estimation") TYPE="TRAINING_energy";;
  "TRAINING/for_particle_classification") TYPE="TRAINING_classification";;
  "DL2") TYPE="DL2";;
esac

# Cycle over particle type
for part in $PARTICLE; do

  # Download files
  echo "Downloading $part..."
  $DIRAC/diracos/usr/bin/python $GRID_INTERFACE/download_files.py --indir="$INPUT_DIR" --outdir="$OUTPUT_DIR"

  # Merge files
  echo "Merging $part..."
  OUTPUT_FILE="$OUTPUT_DIR/${DATA_TYPE}_${MODE}_${part}_merged.h5"
  TEMPLATE_FILE_NAME="${DATA_TYPE}_${part}_${MODE}"
  $DIRAC/diracos/usr/bin/python $GRID_INTERFACE/merge_tables.py --indir="$OUTPUT_DIR" --template_file_name="$TEMPLATE_FILE_NAME" --outfile="$OUTPUT_FILE"

done
