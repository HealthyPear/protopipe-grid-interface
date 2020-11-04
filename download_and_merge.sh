#!/usr/bin/env bash

# ============================================
#           EDIT ONLY THIS PART
# ============================================

# User variables
ANALYSIS_NAME=""
HOME_PATH_GRID="/vo.cta.in2p3.fr/user/x/xxx" # fill this
ANALYSIS_PATH_GRID="" # path from HOME_PATH_GRID, if none leave empty

# ANALYSIS STEP DATA PATH
# Possible choices are,
# - TRAINING/for_energy_estimation
# - TRAINING/for_particle_classification
# - DL2
DATA_PATH=""

PARTICLE=""  # This can be list up to "gamma proton electron"

# ============================================

MODE="tail"  # also "wave" (wavelet) cleaning, but disabled for the moment

ANALYSIS_PATH_LOCAL="/home/vagrant/shared_folder/analyses/$ANALYSIS_NAME"

# DIRAC file catalog full path
INPUT_DIR="$HOME_PATH_GRID/$ANALYSIS_PATH_GRID/$ANALYSIS_NAME/data/$DATA_PATH"
# Full path in local virtual environment for the grid interface
OUTPUT_DIR="$ANALYSIS_PATH_LOCAL/data/$DATA_PATH/"

# FILE TYPE
case $DATA_PATH in
   "TRAINING/for_energy_estimation") TYPE="TRAINING_energy";;
   "TRAINING/for_particle_classification") TYPE="TRAINING_classification";;
   "DL2") TYPE="DL2";;
esac

# Get files
python $GRID/download_files.py --indir="$INPUT_DIR" --outdir="$OUTPUT_DIR"

# Merge files
for part in $PARTICLE; do
    echo "Merging $part..."
    OUTPUT_FILE="$OUTPUT_DIR/${TYPE}_${MODE}_${part}_merged.h5"
    TEMPLATE_FILE_NAME="${TYPE}_${MODE}_${part}"

    echo "$OUTPUT_DIR"
    echo "$TEMPLATE_FILE_NAME"
    echo "$OUTPUT_FILE"

    python $GRID/merge_tables.py --indir="$OUTPUT_DIR" --template_file_name="$TEMPLATE_FILE_NAME" --outfile="$OUTPUT_FILE"
done
