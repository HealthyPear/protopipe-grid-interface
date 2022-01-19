import argparse
import logging
import re
from pathlib import Path

from DIRAC.Interfaces.API.Dirac import Dirac


def main():

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)

    description = """Export input LFNs to file for a job."""

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "--job_id",
        type=int,
        required=True,
        help="ID of the job",
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Path to output_file (default: None --> ID_LFNs.list)",
    )
    args = parser.parse_args()

    if args.output_file is None:
        output_file = f"{args.job_id}_FLNs.list"
    else:
        output_file = Path(args.output_file)

    dirac = Dirac()

    result = dirac.getJobJDL(args.job_id)
    while "Value" not in result.keys():
        result = dirac.getJobJDL(args.job_id)
        logging.debug(result)
    else:
        input_data = result["Value"]["InputData"]
        lfns = [i for i in input_data if not re.compile("estimators").search(i)]

        with open(output_file, mode="w", encoding="utf8") as file:
            for lfn in lfns:
                file.writelines(lfn + "\n")


if __name__ == "__main__":
    main()
