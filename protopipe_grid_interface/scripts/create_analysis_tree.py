"""Create the directory structure for an analysis."""

from __future__ import with_statement
import os
import glob
from pathlib import Path
import argparse
from argparse import RawTextHelpFormatter
import yaml
from pkg_resources import resource_filename
import sys

from protopipe_grid_interface.utils import initialize_logger, makedir


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

    with open(input_file, mode="r", encoding="utf8") as infile:
        with open(output_file, mode="w", encoding="utf8") as outfile:
            for line in infile:
                for old, new in zip(old_text, new_text):
                    line = line.replace(old, new)
                outfile.write(os.path.expandvars(line))


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

    for key, children in dictionary.items():
        if len(children) > 0:
            if isinstance(children, list):
                for child in children:
                    paths.append(os.path.join(key, child))
            elif isinstance(children, dict):
                for child in create_paths(children):
                    paths.append(os.path.join(key, child))
            else:
                raise ValueError(
                    "Analysis workflow must be defined using dictionaries and/or lists of folders."
                )
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
        description=description, formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--analysis_name", type=str, required=True, help="Name of the analysis"
    )

    parser.add_argument(
        "--analysis_directory_tree",
        type=str,
        help="Analysis workflow YAML file (default: see protopipe_grid_interface.aux)",
    )

    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help="""Override log file path
                (default: analysis.log in analysis folder)""",
    )

    parser.add_argument(
        "--output_path",
        type=str,
        default=os.environ["HOME"],
        help="Full path where the 'shared_folder' should be created (or where it already exists)",
    )

    parser.add_argument(
        "--GRID-is-DIRAC",
        action="store_true",
        help="The grid on which to run the analysis is the DIRAC grid.",
    )

    parser.add_argument(
        "--GRID-home",
        type=str,
        default="/vo.cta.in2p3.fr/user/x/xxx",
        help="Path of the user's home on grid (if DIRAC, /vo.cta.in2p3.fr/user/x/xxx).",
    )

    parser.add_argument(
        "--GRID-path-from-home",
        type=str,
        default="",
        help="Path of the analysis on the DIRAC grid. Defaults for empty string (user home)",
    )

    parser.add_argument(
        "--overwrite-analysis",
        action="store_true",
        required=False,
        help="Overwrite analysis folder (WARNING: you could loose data!)",
    )

    args = parser.parse_args()

    # read command-line arguments
    analysis_name = args.analysis_name

    # Define required directories and create them if necessary

    output_path = Path(args.output_path).resolve()

    shared_folder_directory = output_path / "shared_folder"
    analyses_directory = Path(shared_folder_directory) / "analyses"
    productions_directory = Path(shared_folder_directory) / "productions"
    analysis_path = Path(analyses_directory) / analysis_name

    if args.log_file is None:
        log_filepath = (
            Path.cwd() / f"protopipe_temp_creation_of_analysis_{analysis_name}.log"
        )
        Path(log_filepath).touch()
    else:
        log_filepath = Path(args.log_file)
    log = initialize_logger(
        logger_name=__name__, log_filename=log_filepath, append=False
    )

    makedir(shared_folder_directory, overwrite=False, logger=log)
    makedir(analyses_directory, overwrite=False, logger=log)
    makedir(productions_directory, overwrite=False, logger=log)

    # Read analysis workflow and convert it to directory paths
    if args.analysis_directory_tree:
        with open(args.analysis_directory_tree, mode="r", encoding="utf8") as f:
            analysis_directory_tree = yaml.safe_load(f)
    else:
        analysis_directory_file = resource_filename(
            "protopipe_grid_interface", "aux/standard_analysis_workflow.yaml"
        )
        with open(analysis_directory_file, mode="r", encoding="utf8") as stream:
            analysis_directory_tree = yaml.safe_load(stream)

    # Build relative paths for this directory tree
    relative_paths = create_paths(analysis_directory_tree)

    # Create them only if analyses folder was created now
    if (not analysis_path.exists()) or (
        analysis_path.exists() and args.overwrite_analysis
    ):
        # Create analysis folder
        makedir(analysis_path, overwrite=True, logger=log)

        # Write metadata to YAML file and store it into the analysis folder
        log.info("Writing metadata...")
        analysis_metadata = {
            "analyses_directory": str(analyses_directory),
            "analysis_name": analysis_name,
            "GRID is DIRAC": args.GRID_is_DIRAC,
            "Home directory on the GRID": args.GRID_home,
            "analysis directory on the GRID from home": args.GRID_path_from_home,
        }
        with open(
            analyses_directory / analysis_name / "analysis_metadata.yaml",
            mode="w",
            encoding="utf8",
        ) as file:
            yaml.dump(analysis_metadata, file)
        log.info(
            "A YAML file containing metadata for this analysis has been stored in the analysis folder"
        )

        for path in relative_paths:
            full_path = analysis_path / path
            try:
                full_path.mkdir(parents=True, exist_ok=args.overwrite_analysis)
            except os.error as e:
                log.critical(
                    "Creation of the directory %s failed due to %s", full_path, e
                )
                log.critical("Directory structure NOT ready for protopipe analysis.")
                sys.exit()

        log.info("Directory structure ready for protopipe analysis.")

        # Create a grid configuration file for this analysis starting from the example

        if args.GRID_is_DIRAC:
            username = args.GRID_home.split("/")[-1]

        grid_configuration_file_name = "grid.yaml"
        example_grid_configuration_file = resource_filename(
            "protopipe_grid_interface", f"aux/{grid_configuration_file_name}"
        )
        analysis_grid_configuration_file = os.path.join(
            analysis_path, f"configs/{grid_configuration_file_name}"
        )

        setup_config(
            example_grid_configuration_file,
            analysis_grid_configuration_file,
            [
                "ANALYSIS_NAME",
                "LOCAL",
                'user_name: ""',
                'home_grid: ""',
                'outdir: ""',
            ],
            [
                analysis_name,
                str(output_path),
                f'user_name: "{username}"',
                f'home_grid: "{args.GRID_home}"',
                f'outdir: "{args.GRID_path_from_home}"',
            ],
        )

        # Do the same for the rest of the configuration files
        example_config_files = glob.glob(
            f"{resource_filename('protopipe', 'aux/example_config_files/')}/*.yaml"
        )
        for example_config_file in example_config_files:

            config_file_name = Path(example_config_file).name
            configuration_file = os.path.join(
                analysis_path, f"configs/{config_file_name}"
            )

            setup_config(
                example_config_file,
                configuration_file,
                [
                    "ANALYSES_DIRECTORY",
                    "ANALYSIS_NAME",
                ],
                [str(analyses_directory), analysis_name],
            )

        log.info(
            "Auxiliary scripts and configuration files have been stored and partially filled."
        )
        log.debug("Finalizing analysis log file...")
        log_filepath.rename(analysis_path / "analysis.log")
        if not (analysis_path / "analysis.log").exists():
            log.error("Something went wrong with the analysis log file!")
        else:
            log.info("Analysis log file: %s", analysis_path / "analysis.log")

    else:
        log.warning(
            "Required analysis folder exists and no overriding has been requested. Terminating now."
        )


if __name__ == "__main__":
    main()
