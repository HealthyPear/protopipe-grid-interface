import os
import argparse
from argparse import RawTextHelpFormatter
from pathlib import Path
import yaml

from protopipe_grid_interface.utils import initialize_logger, makedir


def main():

    description = """Split a simulation dataset.

    Requirement:
    - list files should have *.list extension.

    Default analysis workflow (see protopipe/aux/standard_analysis_workflow.yaml):
    - a training sample for energy made of gammas,
    - a training sample for particle classification made of gammas and protons,
    - a performance sample made of gammas, protons, and electrons.

    """

    parser = argparse.ArgumentParser(
        description=description, formatter_class=RawTextHelpFormatter
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--metadata",
        type=str,
        default=None,
        help="""Analysis metadata file produced at creation
        (recommended).""",
    )
    group.add_argument(
        "--output_path", type=str, default=None, help="Specifiy an output directory"
    )

    parser.add_argument(
        "--input_gammas", type=str, help="Full path of the original list of gammas."
    )
    parser.add_argument(
        "--input_protons", type=str, help="Full path of the original list of protons."
    )
    parser.add_argument(
        "--input_electrons",
        type=str,
        help="Full path of the original list of electrons.",
    )

    parser.add_argument(
        "--split_gammas",
        nargs="+",
        type=int,
        default=[10, 10, 80],
        help="List of percentage values in which to split the gammas. \
Default is [10,10,80]",
    )
    parser.add_argument(
        "--split_protons",
        nargs="+",
        type=int,
        default=[40, 60],
        help="List of 3 percentage values in which to split the protons. \
Default is [40,60]",
    )
    parser.add_argument(
        "--split_electrons",
        nargs="+",
        type=int,
        default=[100],
        help="List of percentage values in which to split the electrons. \
Default is [100]",
    )

    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help="""Override log file path
                (ignored when using metadata)""",
    )

    args = parser.parse_args()

    # Read metadata if available
    if args.metadata:
        with open(args.metadata, mode="r", encoding="utf8") as f:
            metadata = yaml.safe_load(f)
        analysis_name = metadata["analysis_name"]
        analysis_path_local = Path(metadata["analyses_directory"]) / analysis_name
        outdir = analysis_path_local / "data/simtel"
        log_filepath = analysis_path_local / "analysis.log"
        append = True
    else:
        outdir = Path(args.output_path)
        log_filepath = outdir / "split_datasets.log"
        append = False

    log = initialize_logger(
        logger_name=__name__, log_filename=log_filepath, append=append
    )

    log.debug("Checking for output directory...")
    makedir(outdir, is_analysis=False, overwrite=True, logger=log)
    log.info("Splitted lists will be stored under %s", outdir)

    prodlists = [
        [args.input_gammas, args.split_gammas],
        [args.input_protons, args.split_protons],
        [args.input_electrons, args.split_electrons],
    ]

    particle_types = ["gammas", "protons", "electrons"]
    stages = ["_TRAINING_ENERGY", "_TRAINING_CLASSIFICATION", "_PERFORMANCE"]

    # Cycle on simulation lists
    for i, prodlist in enumerate(prodlists):

        if prodlist[0] is None:
            log.warning("A particle type list seems empty or undefined.")
            continue

        with open(prodlist[0], "r", encoding="utf8") as f:
            prod_lines = f.readlines()

        log.debug(
            "Input list for %s from %s contains %i files...",
            particle_types[i],
            prodlist[0],
            len(prod_lines),
        )

        numlines = [0]

        for prop in prodlist[1][: len(prodlist[1]) - 1]:
            delta = int(prop / 100.0 * len(prod_lines) + 0.5)
            numlines.append(numlines[-1] + delta)

        if len(numlines) != 1:
            log.debug("Split according to file # : %s", numlines)
        else:
            log.debug("All files in 1 list.")

        # Cycle on analysis stages
        for inum, iprop in enumerate(numlines):

            outname = (
                os.path.basename(prodlist[0]).split(".list")[0] + stages[inum] + ".list"
            )

            log.debug("outname: %s", outname)

            if inum + 1 < len(numlines):
                tlines = prod_lines[iprop : numlines[inum + 1]]
            else:
                tlines = prod_lines[iprop:]

            log.debug("Number of files: %s", len(tlines))
            if len(tlines) > 0:
                with open(
                    os.path.join(outdir, outname), mode="w", encoding="utf8"
                ) as f:
                    f.writelines(tlines)

        del stages[0]


if __name__ == "__main__":
    main()
