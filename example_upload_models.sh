#!/usr/bin/env bash

ANALYSIS_NAME=""  # Name of the analysis
MODE="tail"  # Here tail or wave
CAM_IDS='LSTCam NectarCam'  # This is a list
MODEL_TYPE=""  # regressor or classifier
MODEL_NAME=""  # AdaBoostRegressor or RandomForestClassifier

# Full path in local virtual environment for the grid interface
INPUT_DIR="path_to_analysis/$ANALYSIS_NAME/estimators/"
# DIRAC file catalog path
OUTPUT_DIR="/vo.cta.in2p3.fr/user/x/xxx/path_to_analysis/$ANALYSIS_NAME/estimators/"

SE_LIST='DESY-ZN-USER CNAF-USER ' # List of SE, by default copy on CC-kIN2P3

for cam_id in $CAM_IDS; do
    file="${MODEL_TYPE}_${MODE}_${cam_id}_${MODEL_NAME}.pkl.gz"
    echo "Uploading $INPUT_DIR/$file..."
    python $GRID/upload_file.py --indir=$INPUT_DIR --infile=$file --outdir=$OUTPUT_DIR

    # Make replicas
    for SE in $SE_LIST; do
    echo "Making replica on $SE"
        dirac-dms-replicate-lfn $OUTPUT_DIR/$file $SE
    done

done
