#!/usr/bin/env python

import os
import argparse
import subprocess


def main():
    # Read command line options
    parser = argparse.ArgumentParser(description="Upload file(s) on the GRID")
    parser.add_argument("--indir", default=None, help="Input repository")
    parser.add_argument("--infile", default=None, help="Input file")
    parser.add_argument("--outdir", default=None, help="GRID repository")
    args = parser.parse_args()

    file_to_upload = os.path.join(args.indir, args.infile)
    file_on_dirac = os.path.join(args.outdir, args.infile)

    # Get list of files
    batcmd = "dirac-dms-add-file {} {} {}".format(
        file_on_dirac, file_to_upload, "CC-IN2P3-USER"
    )
    result = subprocess.check_output(batcmd, shell=True)
    print(result)


if __name__ == "__main__":
    main()
