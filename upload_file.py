#!/usr/bin/env python

import os
import argparse
import subprocess


def main():
    # Read command line options
    parser = argparse.ArgumentParser(description="Upload collection files from Dirac")
    parser.add_argument("--indir", default=None, help="Input repository")
    parser.add_argument("--infile", default=None, help="Input file")
    parser.add_argument("--outdir", default=None, help="Dirac repository")
    args = parser.parse_args()

    file_to_upload = os.path.join(args.indir, args.infile)
    file_on_dirac = os.path.join(args.outdir, args.infile)
    print("Upload file: {} to {}".format(file_to_upload, file_on_dirac))

    # Get list of files
    batcmd = "dirac-dms-add-file {} {} {}".format(
        file_on_dirac, file_to_upload, "CC-IN2P3-USER"
    )
    result = subprocess.check_output(batcmd, shell=True)
    file_list = result.split()[-1]

    print(f"Result of the operation = {result}")
    print(f"Files concerned by this operation = {file_list}")


if __name__ == "__main__":
    main()
