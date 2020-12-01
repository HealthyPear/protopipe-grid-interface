"""Create the directory structure for an analysis."""

import os
import glob
import argparse
from argparse import RawTextHelpFormatter
import shutil


def makedir(name):
    """
    Create folder if non-existent and output OS error if any.

    Parameters
    ----------
    name : str
        Name of the analysis.

    """
    if not os.path.exists(name):
        try:
            os.mkdir(name)
        except OSError:
            print("Creation of the directory {} failed".format(name))
        else:
            print("Successfully created the directory {}".format(name))
    return None


def main():

    # define command-line arguments

    description = """Create a directory structure for a CTA data analysis \
using the protopipe prototype pipeline.

    WARNING: check that the version of protopipe is the one you intend to use!

    """

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--analysis_name", type=str, required=True, help="Name of the analysis"
    )

    args = parser.parse_args()

    # read command-line arguments
    analysisName = args.analysis_name

    # Create analysis parent folder
    analysisPath = "/home/vagrant/shared_folder/analyses"
    analysis = os.path.join(analysisPath, analysisName)
    makedir(analysis)

    # Define analysis subdirectories
    subdirectories = {
        "configs": [],
        "data": ["simtel", "TRAINING", "DL2", "DL3"],
        "estimators": ["energy_regressor", "gamma_hadron_classifier"],
    }

    # Create them
    for d in subdirectories:
        subdir = os.path.join(analysis, d)
        makedir(subdir)
        for dd in subdirectories[d]:
            subsubdir = os.path.join(subdir, dd)
            makedir(subsubdir)
            if dd == "TRAINING":
                makedir(os.path.join(subsubdir, "for_particle_classification"))
                makedir(os.path.join(subsubdir, "for_energy_estimation"))

    print("Directory structure ready for protopipe analysis on DIRAC.")

    # Source code paths
    interface_path = "/home/vagrant/protopipe-grid-interface"
    protopipe_path = "/home/vagrant/protopipe"
    protopipe_configs = os.path.join(
        protopipe_path, "protopipe/aux/example_config_files/"
    )

    # Copy scripts
    shutil.copy(
        os.path.join(interface_path, "download_and_merge.sh"),
        os.path.join(analysis, "data"),
    )
    shutil.copy(
        os.path.join(interface_path, "upload_models.sh"),
        os.path.join(analysis, "estimators"),
    )

    # Copy configuration files
    shutil.copy(
        os.path.join(interface_path, "grid.yaml"), os.path.join(analysis, "configs")
    )
    for config_file in glob.glob(os.path.join(protopipe_configs, "*.yaml")):
        shutil.copy(
            config_file, os.path.join(analysis, "configs")
        )

    print("Auxiliary scripts and configuration file are also stored there.")


if __name__ == "__main__":
    main()
