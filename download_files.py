#!/usr/bin/env python

import argparse
import subprocess
import os
from DIRAC.Interfaces.API.Dirac import Dirac


def main():
    # Read command line options
    parser = argparse.ArgumentParser(description="Download collection files from Dirac")
    parser.add_argument("--indir", default=None, help="Dirac repository")
    parser.add_argument("--outdir", default="", help="Output file directory")
    args = parser.parse_args()

    print("Download file from: {}".format(args.indir))
    print("Output directory: {}".format(args.outdir))

    # Create output directory
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    # Get list of files
    batcmd = "dirac-dms-user-lfns --BaseDir {}".format(args.indir)
    result = subprocess.check_output(batcmd, shell=True)
    file_list = result.split()[-1]

    # try reading the lfns file
    try:
        grid_file_list = open(file_list)
    except IOError:
        raise IOError("cannot read lfns file list...")

    dirac = Dirac()

    file_collection = []
    for line in grid_file_list.read().splitlines():

        if len(file_collection) < 100:
            file_collection.append(line)  # files will be downloaded later
        else:
            dirac.getFile(file_collection, destDir=args.outdir)
            file_collection = []  # there won't be any loop at the end

    if file_collection:
        dirac.getFile(file_collection, destDir=args.outdir)


if __name__ == "__main__":
    main()
