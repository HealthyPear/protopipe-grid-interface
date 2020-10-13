#!/usr/bin/env bash

ANALYSIS_NAME=""  # Name of the analysis
HOME_PATH_GRID="/vo.cta.in2p3.fr/user/x/xxx/"
ANALYSIS_PATH_GRID="" # path from HOME_PATH_GRID to the analysis folder
MODE="tail"  # Here tail (tailcut) or wave (wavelet) cleaning
CAM_IDS=''  # This is a list
MODEL_TYPE=""  # regressor or classifier
MODEL_NAME=""  # AdaBoostRegressor or RandomForestClassifier

# Full path in local virtual environment for the grid interface
INPUT_DIR="home/vagrant/shared_folder/analyses/$ANALYSIS_NAME/estimators"
# DIRAC file catalog path
OUTPUT_DIR="$HOME_PATH_GRID/$ANALYSIS_PATH_GRID/$ANALYSIS_NAME/estimators/"

SE_LIST='DESY-ZN-USER CNAF-USER ' # List of SE, by default copy on CC-IN2P3

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
