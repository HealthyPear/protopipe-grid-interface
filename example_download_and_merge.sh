#!/usr/bin/env bash

# User variables
ANALYSIS_NAME=""  # Name of the analysis
TYPE="dl2"  # Here dl1 or dl2
FILE_TYPE="dl2"  # Here dl1_energy, dl1_discrimination, dl2, dl2_force_tc_extended_cleaning
MODE="tail"  # Here, tail, wave
PARTICLE='gamma '  # This can be list, gamma, proton, electron

# DIRAC file catalog full path
INPUT_DIR="/vo.cta.in2p3.fr/user/x/xxx/path_to_analysis/$ANALYSIS_NAME/$FILE_TYPE"
# Full path in local virtual environment for the grid interface
OUTPUT_DIR="path_to_my_config/$ANALYSIS_NAME/data/$FILE_TYPE/"

# Get files
python $GRID/download_files.py --indir=$INPUT_DIR --outdir=$OUTPUT_DIR

# Merge files
for part in $PARTICLE; do
    echo "Merging $part..."
    OUTPUT_FILE="$OUTPUT_DIR/${TYPE}_${MODE}_${part}_merged.h5"
    TEMPLATE_FILE_NAME="${TYPE}_${MODE}_${part}"

    echo $OUTPUT_DIR
    echo $TEMPLATE_FILE_NAME
    echo $OUTPUT_FILE

    python $GRID/merge_tables.py --indir=$OUTPUT_DIR --template_file_name=$TEMPLATE_FILE_NAME --outfile=$OUTPUT_FILE
done
