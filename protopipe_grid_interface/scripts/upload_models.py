import argparse
from argparse import RawTextHelpFormatter
from pathlib import Path
import subprocess
import yaml

from protopipe_grid_interface.utils import initialize_logger, upload


def main():

    description = """Upload models produced with protopipe to the Dirac grid.

    Files will be uploaded at least on CC-IN2P3-USER.
    You can use `cta-prod-show-dataset YOUR_DATASET_NAME --SEUsage` to know
    on which Dirac Storage Elements to replicate you models.
    Note: you will see *-Disk entries, but you need to replicate using *-USER entries.
    The default behaviour is replicate them to "DESY-ZN-USER", "CNAF-USER", "CEA-USER".
    Replication is optional.
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
        "--cameras",
        type=str,
        required=True,
        nargs="+",
        help="List of cameras to consider",
    )
    parser.add_argument(
        "--model_type",
        type=str,
        required=True,
        choices=["regressor", "classifier"],
        help="Type of model to upload",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        choices=[
            "RandomForestRegressor",
            "AdaBoostRegressor",
            "RandomForestClassifier",
        ],
        help="Type of model to upload",
    )
    parser.add_argument(
        "--cleaning_mode", type=str, default="tail", help="Deprecated argument"
    )

    parser.add_argument(
        "--GRID-home",
        type=str,
        help="Path of the user's home on grid: /vo.cta.in2p3.fr/user/x/xxx (recommended: use metadata file).",
    )

    parser.add_argument(
        "--GRID-path-from-home",
        type=str,
        default="",
        help="Analysis path on DIRAC grid (defaults to user's home; recommended: use metadata file)",
    )
    parser.add_argument(
        "--list-of-SEs",
        type=str,
        default=["DESY-ZN-USER", "CNAF-USER", "CEA-USER"],
        nargs="*",
        help="List of DIRAC Storage Elements which will host the uploaded models",
    )

    parser.add_argument(
        "--analysis_name",
        type=str,
        help="Name of the analysis (recommended: use metadata file)",
    )

    parser.add_argument(
        "--local_path",
        type=str,
        default="",
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

    # Read metadata if set
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

    model_type_folder = {
        "regressor": "energy_regressor",
        "classifier": "gamma_hadron_classifier",
    }

    analysis_configuration_directory = analysis_path_local / "configs"
    input_directory = (
        analysis_path_local / "estimators" / model_type_folder[args.model_type]
    )
    output_directory = grid_home / grid_path_from_home / analysis_name / "estimators"

    # Upload configuration file
    configuration_file = f"{args.model_name}.yaml"
    log.info(
        "Uploading %s from %s to %s",
        configuration_file,
        analysis_configuration_directory,
        output_directory,
    )
    upload(analysis_configuration_directory, configuration_file, output_directory)
    # Make replicas
    for se in args.list_of_SEs:
        log.info("Producing replicas of %s on %s", configuration_file, se)
        try:
            result = subprocess.run(
                [
                    "dirac-dms-replicate-lfn",
                    str(output_directory / configuration_file),
                    se,
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            log.debug(result)
        except subprocess.CalledProcessError as e:
            log.error("Exit status: %s", e.returncode)
            log.error("Command: %s", e.cmd)
            log.error("STDOUT: %s", e.stdout)
            log.error("STDERR: %s", e.stderr)

    # Upload model files
    for camera in args.cameras:

        model_file = f"{args.model_type}_{camera}_{args.model_name}.pkl.gz"
        log.info(
            "Uploading %s from %s to %s...",
            model_file,
            input_directory,
            output_directory,
        )
        upload(input_directory, model_file, output_directory)

        # Make replicas
        for se in args.list_of_SEs:
            log.info("Producing replicas of %s on %s...", model_file, se)
            try:
                result = subprocess.run(
                    ["dirac-dms-replicate-lfn", str(output_directory / model_file), se],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                log.debug(result)
            except subprocess.CalledProcessError as e:
                log.error("Exit status: %s", e.returncode)
                log.error("Command: %s", e.cmd)
                log.error("STDOUT: %s", e.stdout)
                log.error("STDERR: %s", e.stderr)

    log.info("Models and configuration files have been uploaded.")


if __name__ == "__main__":
    main()
