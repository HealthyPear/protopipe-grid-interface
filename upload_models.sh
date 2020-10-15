#!/usr/bin/env bash

ANALYSIS_NAME=""  # Name of the analysis
ANALYSES_PATH="/home/vagrant/shared_folder/analyses"
HOME_PATH_GRID="/vo.cta.in2p3.fr/user/x/xxx"
ANALYSIS_PATH_GRID="" # path from HOME_PATH_GRID to the analysis folder
MODE="tail"  # Here tail (tailcut) or wave (wavelet) cleaning
CAM_IDS=''  # This is a list
MODEL_TYPE=""  # regressor or classifier
MODEL_NAME=""  # AdaBoostRegressor or RandomForestClassifier

# For the moment estimators are stored all together on the GRID
# but locally keeping them separated makes the analysis directory more clear.
if [[ $MODEL_TYPE = "regressor" ]]
then
  MODEL_TYPE_FOLDER="energy_regressor"
else
  MODEL_TYPE_FOLDER="gamma_hadron_classifier"
fi

# Full path in local virtual environment for the grid interface
INPUT_DIR="$ANALYSES_PATH/$ANALYSIS_NAME/estimators/$MODEL_TYPE_FOLDER"
# DIRAC file catalog path
OUTPUT_DIR="$HOME_PATH_GRID/$ANALYSIS_PATH_GRID/$ANALYSIS_NAME/estimators/"

# List of SE, by default copy on CC-IN2P3
SE_LIST='DESY-ZN-USER CNAF-USER CEA-USER '

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
