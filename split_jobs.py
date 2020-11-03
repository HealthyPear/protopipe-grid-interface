#!/usr/bin/env python

import re
import os
import argparse
from argparse import RawTextHelpFormatter


def makedir(name):
    """Create folder if non-existent and output OS error if any.

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
    else:
        print("Using existing folder {}".format(name))
    return None


def main():

    description = """Split a simulation dataset.

    Requirement:
    - list files should have *.list extension.

    Current scheme for a protopipe analysis:
    - a training sample for energy made of gammas,
    - a training sample for particle classification made of gammas and protons,
    - a performance sample made of gammas, protons, and electrons.

    """

    parser = argparse.ArgumentParser(
        description=description, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument("--debug",
                        action="store_true",
                        help="Print debug information")

    parser.add_argument(
        "--input_gammas",
        type=str,
        help="Full path of the original list of gammas."
    )
    parser.add_argument(
        "--input_protons",
        type=str,
        help="Full path of the original list of protons."
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
        "--output_path",
        type=str,
        required=False,
        default=None,
        help="Folder or path under /home/vagrant/productions.",
    )

    args = parser.parse_args()

    print("Checking for output directory...")
    outdir = os.path.join("/home/vagrant/shared_folder/productions", args.output_path)
    makedir(outdir)
    print("Splitted lists will be stored under {}".format(outdir))

    prodlists = [
        [args.input_gammas, args.split_gammas],
        [args.input_protons, args.split_protons],
        [args.input_electrons, args.split_electrons],
    ]

    particle_types = ["gammas", "protons", "electrons"]
    stages = ["_TRAINING_ENERGY", "_TRAINING_CLASSIFICATION", "_PERFORMANCE"]

    # Cycle on simulation lists
    for i, prodlist in enumerate(prodlists):

        flist = open(prodlist[0], "r")
        prodLines = flist.readlines()
        flist.close()

        numlines = [1]

        for prop in prodlist[1][: len(prodlist[1]) - 1]:
            delta = int(prop / 100.0 * len(prodLines) + 0.5)
            numlines.append(numlines[-1] + delta)

        if args.debug:
            print("Input list for {} from {}".format(particle_types[i], prodlist[0]))
            print("\tSplitted according to line numbers : {}".format(numlines))

        # Cycle on analysis stages
        for inum, iprop in enumerate(numlines):

            outname = os.path.basename(prodlist[0]).split(".list")[0] + stages[inum] + ".list"

            if args.debug:
                print("DEBUG>> outname: {}".format(outname))

            if inum + 1 < len(numlines):
                Tlines = prodLines[iprop: numlines[inum + 1]]
            else:
                Tlines = prodLines[iprop:]

            if args.debug:
                print("DEBUG>> Number of files: {}".format(len(Tlines)))
            if len(Tlines) > 0:
                fprop = open(os.path.join(outdir, outname), "w")
                for line in Tlines:
                    print >> fprop, line.strip()
                fprop.close()

        del stages[0]

if __name__ == "__main__":
    main()
