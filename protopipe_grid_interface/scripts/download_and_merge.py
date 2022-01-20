import argparse
from argparse import RawTextHelpFormatter
import glob
from pathlib import Path
import subprocess

import yaml

from protopipe_grid_interface.scripts.merge_tables import merge_call
from protopipe_grid_interface.utils import initialize_logger, download


def main():
    # Read command line options

    description = """Download and merge data from the DIRAC grid.

    The default behaviour calls an rsync-like command after the normal download as
    an additional check.

    This script can be used separately, or in association with an analysis workflow.
    In the second case the recommended usage is via the metadata file produced at creation.
    """

    parser = argparse.ArgumentParser(
        description=description, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--metadata",
        type=str,
        default=None,
        help="""Path to the metadata file produced at analysis creation
        (recommended - if None, specify necessary information).""",
    )

    parser.add_argument(
        "--disable_download",
        action="store_true",
        help="Do not download files serially",
    )
    parser.add_argument(
        "--disable_sync",
        action="store_true",
        help="Do not syncronyze folders after serial download",
    )
    parser.add_argument(
        "--disable_merge",
        action="store_true",
        help="Do not merge files at the end",
    )

    parser.add_argument(
        "--indir", type=str, default=None, help="Override input directory"
    )
    parser.add_argument(
        "--outdir", type=str, default=None, help="Override output directory"
    )
    parser.add_argument(
        "--data_type",
        type=str,
        required=True,
        choices=[
            "TRAINING/for_energy_estimation",
            "TRAINING/for_particle_classification",
            "DL2",
        ],
        help="Type of data to download and merge",
    )

    parser.add_argument(
        "--particle_types",
        type=str,
        default=None,
        required=True,
        nargs="*",
        choices=["gamma", "proton", "electron"],
        help="One of more particle type to download and merge",
    )

    parser.add_argument(
        "--n_jobs",
        type=int,
        default=1,
        help="Number of parallel jobs for directory syncing (default: 4)",
    )

    parser.add_argument(
        "--cleaning_mode",
        type=str,
        default="tail",
        help="Deprecated argument",
    )

    parser.add_argument(
        "--GRID-home",
        type=str,
        default=None,
        help="""Path of the user's home on DIRAC grid (/vo.cta.in2p3.fr/user/x/xxx)
                (recommended: use metadata file)""",
    )

    parser.add_argument(
        "--GRID-path-from-home",
        type=str,
        default="",
        help="optional additional path from user's home in DIRAC (recommended: use metadata file)",
    )

    parser.add_argument(
        "--analysis_name",
        type=str,
        default=None,
        help="Name of the analysis (recommended: use metadata file)",
    )

    parser.add_argument(
        "--local_path",
        type=str,
        default=None,
        help="Path where shared_folder is located (recommended: use metadata file)",
    )
    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help="""Override log file path
                (default: analysis.log in analysis folder)""",
    )

    args = parser.parse_args()

    # Define data type for analysis
    data_type = {
        "TRAINING/for_energy_estimation": "TRAINING_energy",
        "TRAINING/for_particle_classification": "TRAINING_classification",
        "DL2": "DL2",
    }

    if args.metadata:
        with open(args.metadata, mode="r", encoding="utf8") as f:
            metadata = yaml.safe_load(f)
        analysis_name = metadata["analysis_name"]
        analysis_path_local = Path(metadata["analyses_directory"]) / analysis_name
        grid_home = Path(metadata["Home directory on the GRID"])
        grid_path_from_home = Path(metadata["analysis directory on the GRID from home"])
    else:
        local = Path(args.local_path)
        analysis_name = args.analysis_name
        analysis_path_local = local / "shared_folder/analyses" / analysis_name
        grid_home = Path(args.GRID_home)
        grid_path_from_home = Path(args.GRID_path_from_home)

    if args.log_file is None:
        log_filepath = analysis_path_local / "analysis.log"
        append = True
    else:
        log_filepath = Path(args.log_file)
        append = False
    log = initialize_logger(
        logger_name=__name__, log_filename=log_filepath, append=append
    )

    # for each particle type selected
    for part in args.particle_types:

        log.info("Processing %s...", part)

        # DIRAC file catalog full path
        input_directory = (
            grid_home
            / grid_path_from_home
            / analysis_name
            / "data"
            / Path(args.data_type)
            / part
        )
        # Full path in local virtual environment for the grid interface
        output_directory = analysis_path_local / "data" / args.data_type / part

        # Download files
        if not args.disable_download:
            log.info("Downloading %s...", part)
            log.debug("...from %s", input_directory)
            log.debug("...to %s", output_directory)
            download(str(input_directory), str(output_directory))
            n_files = len(glob.glob(str(output_directory / "*.h5")))
            log.info("%i files have been downloaded into %s", n_files, output_directory)
        # Syncing (for good measure)
        if not args.disable_sync:
            log.info("Syncing directory to be sure...")
            subprocess.check_call(
                [
                    "dirac-dms-directory-sync",
                    "-D",
                    f"-j {args.n_jobs}",
                    str(input_directory),
                    str(output_directory),
                ]
            )

        # Merging files
        if not args.disable_merge:
            log.info("Merging %s...", part)
            output_file = (
                output_directory
                / f"{data_type[args.data_type]}_{args.cleaning_mode}_{part}_merged.h5"
            )
            template_file_name = (
                f"{data_type[args.data_type]}_{part}_{args.cleaning_mode}"
            )
            log.debug("template_file_name = %s", template_file_name)
            merge_call(template_file_name, output_directory, output_file, logger=log)

            log.info("Downloaded files have been merged into %s", output_file)


if __name__ == "__main__":
    main()
