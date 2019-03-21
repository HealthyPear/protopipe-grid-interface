#!/usr/bin/env bash

CONFIG="myconfig"  # Name of the configuration
MODE="tail"  # Here tail or wave
CAM_IDS='LSTCam NectarCam'  # This is a list
MODEL_TYPE="classifier"  # Here regressor or classifier
MODEL_NAME="RandomForestClassifier"  # Here AdaBoostRegressor or RandomForestClassifier

INPUT_DIR="path_to_my_config/$CONFIG/models/"
OUTPUT_DIR="/vo.cta.in2p3.fr/user/x/xxx/path_to_my_config/$CONFIG/models/"

SE_LIST='DESY-ZN-USER CNAF-USER ' # List of SE, by default copy on CC-kIN2P3

for cam_id in $CAM_IDS; do
    file="${MODEL_TYPE}_${MODE}_${cam_id}_${MODEL_NAME}.pkl.gz"
    echo "Uploading $INPUT_DIR/$file..."
    python upload_file.py --indir=$INPUT_DIR --infile=$file --outdir=$OUTPUT_DIR

    # Make replicas
    for SE in $SE_LIST; do
    echo "Making replica on $SE"
        dirac-dms-replicate-lfn $OUTPUT_DIR/$file $SE
    done

done
