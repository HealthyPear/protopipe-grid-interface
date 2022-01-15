import argparse
import subprocess


def main():
    # Read command line options
    parser = argparse.ArgumentParser(description="Delete collection files from Dirac")
    parser.add_argument("--indir", default=None, help="Dirac repository")
    args = parser.parse_args()

    print("Delete file from: {}".format(args.indir))

    # Get list of files
    batcmd = "dirac-dms-user-lfns --BaseDir {}".format(args.indir)
    result = subprocess.check_output(batcmd, shell=True)
    file_list = result.split()[-1]

    # try reading the lfns file
    try:
        grid_file_list = open(file_list)
    except IOError:
        raise IOError("cannot read lfns file list...")

    # Delete files
    batcmd = "dirac-dms-remove-files {}".format(file_list)
    result = subprocess.check_output(batcmd, shell=True)


if __name__ == "__main__":
    main()
