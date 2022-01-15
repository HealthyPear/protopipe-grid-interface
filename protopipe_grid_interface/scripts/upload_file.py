import argparse
import logging

from protopipe_grid_interface.utils import upload

DEFAULT_SE = "CC-IN2P3-USER"


def main():

    parser = argparse.ArgumentParser(description="Upload file(s) on the GRID")
    parser.add_argument("--indir", required=True, help="Input repository")
    parser.add_argument("--infile", required=True, help="Input file")
    parser.add_argument("--outdir", required=True, help="GRID repository")
    parser.add_argument("--SE", default=DEFAULT_SE, help="DIRAC Storage Element")
    parser.add_argument(
        "--loglevel_stream",
        type=str,
        default="INFO",
        choices=["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level on terminal",
    )
    parser.add_argument(
        "--loglevel_file",
        type=str,
        default="DEBUG",
        choices=["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level to file",
    )
    args = parser.parse_args()

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)  # ensures that everything will be logged

    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")

    fh = logging.FileHandler(
        f"upload_{args.model_type}.log", mode="w", encoding="utf-8"
    )
    fh.setLevel(getattr(logging, args.loglevel_file))
    fh.setFormatter(formatter)
    log.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, args.loglevel_stream))
    ch.setFormatter(formatter)
    log.addHandler(ch)

    upload(args.indir, args.infile, args.outdir, args.SE)


if __name__ == "__main__":
    main()
