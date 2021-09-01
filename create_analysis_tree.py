"""Create the directory structure for an analysis."""

from __future__ import with_statement
import os
import glob
import argparse
from argparse import RawTextHelpFormatter
import shutil
import logging


def setup_config(input_file, output_file, old_text, new_text):
    """Fill a configuration file for an analysis starting from the example one.

    Parameters
    ----------
    input_file: str
        Path of the input configuration file.
    output_file: str
        Path of the output configuration file.
    old_text: str
        Text to replace.
    new_text: str
        Text to be used.
    """
    with open(input_file, "r") as infile:
            with open(output_file, "w") as outfile:
                for line in infile:
                    for old, new  in zip(old_text, new_text):
                        line = line.replace(old, new)
                    outfile.write(os.path.expandvars(line))


def makedir(name):
    """
    Manage the creation of a new folder.

    Parameters
    ----------
    name : str
        Name of the folder to be created.
    result: int
        1 for success, 0 otherwise (any reason).

    """
    if not os.path.exists(name):
        try:
            os.mkdir(name)
        except OSError as e:
            logging.critical("Creation of the directory {} failed due to {}".format(name, e))
            return 0
        else:
            logging.info("Successfully created the directory {}".format(name))
            return 1
    else:
        logging.warning("Directory {} already exists and it won't be overwritten.".format(name))
        return 0


def create_paths(dictionary):
    """Create the relative paths of all leaves of a directory tree.

    Parameters
    ----------
    dictionary : dict
        Dictionary representing the directory tree to be created.

    Returns
    -------
    paths : list
        List of relative paths
    """
    paths = []

    for key, children in dictionary.iteritems():
        if len(children) > 0:
            for child in children:
                if isinstance(child, dict):
                    for grandchild in create_paths(child):
                        paths.append(os.path.join(key, grandchild))
                else:
                    paths.append(os.path.join(key, child))
        else:
            paths.append(os.path.join(key))
    return paths


def main():

    description = """Create a directory structure for a CTA data analysis \
using the protopipe prototype pipeline.

    WARNING: check that the version of protopipe is the one you intend to use!

    """

    # Define arguments' parser
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--analysis_name", type=str, required=True, help="Name of the analysis"
    )

    parser.add_argument(
        "--GRID-is-DIRAC", action='store_true', help="The grid on which to run the analysis is the DIRAC grid."
    )

    parser.add_argument(
        "--GRID-home", type=str, default="/vo.cta.in2p3.fr/user/x/xxx", help="Path of the user's home on grid (if DIRAC, /vo.cta.in2p3.fr/user/x/xxx)."
    )
    
    parser.add_argument(
        "--GRID-path-from-home", type=str, default="", help="Path of the analysis on the DIRAC grid. Defaults for empty string (user home)"
    )

    args = parser.parse_args()

    # read command-line arguments
    analysis_name = args.analysis_name

    # Get home's absolute path
    home_path = os.environ['HOME']

    # Define required directories and create them if necessary

    shared_folder_directory = os.path.join(home_path, "shared_folder")
    makedir(shared_folder_directory)

    analyses_directory = os.path.join(shared_folder_directory, "analyses")
    makedir(analyses_directory)

    productions_directory = os.path.join(shared_folder_directory, "productions")
    makedir(productions_directory)

    analysis_path = os.path.join(analyses_directory, analysis_name)
    new_analysis = makedir(analysis_path)

    # Define analysis subdirectories
    # (it could be read as a dictionary from a JSON file if multiple analysis workflows are introduced)
    subdirectories = {
        "configs": [],
        "data": ["simtel",
                    {"TRAINING": ["for_energy_estimation",
                                  "for_particle_classification"]},
                     "DL2",
                     "DL3"],
        "estimators": ["energy_regressor", "gamma_hadron_classifier"],
    }
    # Build relative paths for this directory tree
    relative_paths = create_paths(subdirectories)

    # Create them only if analyses folder was created now
    if new_analysis:

        for path in relative_paths:
            full_path = os.path.join(analysis_path, path)
            try:
                os.makedirs(full_path)
            except os.error as e:
                logging.critical("Creation of the directory {} failed due to {}".format(full_path, e))
                logging.critical("Directory structure NOT ready for protopipe analysis.")
                exit()

        logging.info("Directory structure ready for protopipe analysis.")

        # Source code paths
        interface_path = os.path.join(home_path, "protopipe-grid-interface")
        protopipe_path = os.path.join(home_path, "protopipe")
        protopipe_configs = os.path.join(
            protopipe_path, "protopipe/aux/example_config_files/"
        )

        # Copy scripts and edit scripts according to this analysis
        
        setup_config(os.path.join(interface_path, "download_and_merge.sh"),
                     os.path.join(analysis_path, "data/download_and_merge.sh"),
                     ['ANALYSIS_NAME=""',
                      'HOME_PATH_GRID=""',
                      'ANALYSIS_PATH_GRID=""'],
                     ['ANALYSIS_NAME="{}"'.format(analysis_name),
                      'HOME_PATH_GRID="{}"'.format(args.GRID_home),
                      'ANALYSIS_PATH_GRID="{}"'.format(args.GRID_path_from_home)]
                     )
        
        setup_config(os.path.join(interface_path, "upload_models.sh"),
                     os.path.join(analysis_path, "estimators/upload_models.sh"),
                     ['ANALYSIS_NAME=""',
                      'HOME_PATH_GRID=""',
                      'ANALYSIS_PATH_GRID=""'],
                     ['ANALYSIS_NAME="{}"'.format(analysis_name),
                      'HOME_PATH_GRID="{}"'.format(args.GRID_home),
                      'ANALYSIS_PATH_GRID="{}"'.format(args.GRID_path_from_home)]
                     )

        # Create a grid configuration file for this analysis starting from the example in protopipe

        if args.GRID_is_DIRAC:
            username = args.GRID_home.split("/")[-1]

        setup_config(os.path.join(interface_path, "grid.yaml"),
                     os.path.join(analysis_path, "configs/grid.yaml"),
                     ["$ANALYSIS_NAME",
                      "$HOME",
                      "user_name: ''",
                      "home_grid: ''",
                      "outdir: ''"],
                     [analysis_name,
                      home_path,
                      "user_name: '{}'".format(username),
                      "home_grid: '{}'".format(args.GRID_home),
                      "outdir: '{}'".format(args.GRID_path_from_home)
                      ]
                     )
        
        # Same with the analysis configuration file
        setup_config(os.path.join(protopipe_configs, "analysis.yaml"),
                     os.path.join(analysis_path, "configs/analysis.yaml"),
                     ["config_name: ''"],
                     ["config_name: '{}'".format(analysis_name)]
                     )

        # Same with the benchmarks configuration file
        setup_config(os.path.join(protopipe_configs, "benchmarks.yaml"),
                     os.path.join(analysis_path, "configs/benchmarks.yaml"),
                     ["analysis_name: ''"],
                     ["analysis_name: '{}'".format(analysis_name)]
                     )

        # copy all other configuration files
        # these will require to work outside of the container untile CTADIRAC supports Python3
        for config_file in glob.glob(os.path.join(protopipe_configs, "*.yaml")):
            if ("analysis" in config_file) or ("benchmarks" in config_file):
                continue
            shutil.copy(
                config_file, os.path.join(analysis_path, "configs")
            )

        logging.info("Auxiliary scripts and configuration file are also stored there.")

    else:
        logging.info("Required analysis folder already present. For safety no sub-directory will be overwritten.")


if __name__ == "__main__":
    main()
