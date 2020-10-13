"""Ctapipe/protopipe analysis directory structure.

Author: Dr. Michele Peresano
Affilitation: CEA-Saclay/Irfu

"""

import os
import argparse


def makedir(name):
    """Create folder if non-existent and output OS error if any."""
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

    parser = argparse.ArgumentParser(
        description="Create a directory structure for a CTA data analysis using the protopipe prototype pipeline."
    )

    parser.add_argument(
        "--analysis_path",
        type=str,
        required=True,
        help="The local path of your analysis in the virtual environment.",
    )
    parser.add_argument(
        "--analysis_name", type=str, required=True, help="The name of your analysis"
    )

    args = parser.parse_args()

    # read command-line arguments
    analysisPath = args.analysis_path
    analysisName = args.analysis_name

    # Create analysis parent folder
    analysis = os.path.join(analysisPath, analysisName)
    makedir(analysis)

    subdirectories = {
        "configs": [],
        "data": ["simtel", "DL1", "DL2", "DL3"],
        "estimators": ["energy_regressor", "gamma_hadron_classifier"],
        "performance": [],  # performance script will create the subdirectories
    }

    for d in subdirectories:
        subdir = os.path.join(analysis, d)
        makedir(subdir)
        for dd in subdirectories[d]:
            subsubdir = os.path.join(subdir, dd)
            makedir(subsubdir)
            if dd == "DL1":
                makedir(os.path.join(subsubdir, "for_classification"))
                makedir(os.path.join(subsubdir, "for_energy_estimation"))

    print("Directory structure ready for protopipe analysis on DIRAC.")


if __name__ == "__main__":
    main()
