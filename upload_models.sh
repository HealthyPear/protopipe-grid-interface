#!/usr/bin/env bash

# ============================================
#             EDIT ONLY THIS PART
# ============================================

CAM_IDS=''  # This is a list
MODEL_TYPE=""  # regressor or classifier
MODEL_NAME=""  # RandomForestRegressor, AdaBoostRegressor or RandomForestClassifier

# ============================================
#             DO NOT EDIT THIS PART
# ============================================

MODE="tail"  # also "wave" (wavelet) cleaning, but disabled for the moment

# For the moment estimators are stored all together on the GRID
# but locally keeping them separated makes the analysis directory more clear.
if [[ $MODEL_TYPE = "regressor" ]]
then
  MODEL_TYPE_FOLDER="energy_regressor"
else
  MODEL_TYPE_FOLDER="gamma_hadron_classifier"
fi

# GRID environment variables
HOME_PATH_GRID=""
ANALYSIS_PATH_GRID=""

# ANALYSIS environment variables
LOCAL="" # Parent directory containing the 'shared_folder'
ANALYSIS_NAME=""  # Name of the analysis
ANALYSES_PATH="$LOCAL/shared_folder/analyses"
CONFIG_DIR="$ANALYSES_PATH/$ANALYSIS_NAME/configs"
INPUT_DIR="$ANALYSES_PATH/$ANALYSIS_NAME/estimators/$MODEL_TYPE_FOLDER"
# DIRAC file catalog path
OUTPUT_DIR="$HOME_PATH_GRID/$ANALYSIS_PATH_GRID/$ANALYSIS_NAME/estimators"

# List of SE, by default copy on CC-IN2P3
SE_LIST='DESY-ZN-USER CNAF-USER CEA-USER '

for cam_id in $CAM_IDS; do
    config="${MODEL_NAME}.yaml"
    file="${MODEL_TYPE}_${cam_id}_${MODEL_NAME}.pkl.gz"

    $DIRAC/diracos/usr/bin $GRID_INTERFACE/upload_file.py --indir=$CONFIG_DIR --infile=$config --outdir=$OUTPUT_DIR
    $DIRAC/diracos/usr/bin $GRID_INTERFACE/upload_file.py --indir=$INPUT_DIR --infile=$file --outdir=$OUTPUT_DIR

    # Make replicas
    for SE in $SE_LIST; do
    echo "Making replica on $SE"
        dirac-dms-replicate-lfn $OUTPUT_DIR/$file $SE
        dirac-dms-replicate-lfn $OUTPUT_DIR/$config $SE
    done

done
