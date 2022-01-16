import argparse
from protopipe_grid_interface.utils import check_voms, download


def main():

    check_voms()

    # Read command line options
    parser = argparse.ArgumentParser(description="Download collection files from Dirac")
    parser.add_argument("--indir", default=None, help="Dirac repository")
    parser.add_argument("--outdir", default="", help="Output file directory")
    args = parser.parse_args()

    download(args.indir, args.outdir)


if __name__ == "__main__":
    main()
