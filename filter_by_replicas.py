import subprocess
import argparse
from argparse import RawTextHelpFormatter
from tqdm import tqdm

def main():

    description = """Filter a list of files by the disk(s) in which they have 
    been replicated.
    """

    # Define arguments' parser
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument(
        "--input_list", type=str, required=True, help="Input list to filter"
    )
    parser.add_argument(
        "--filter_disks", nargs='+', required=True,
        help="List of disks to query (e.g. CC-IN2P3-Disk, DESY-ZN-Disk or CEA-Disk)"
    )
    parser.add_argument(
        "--outfile", type=str, required=True,
        help="Full path of the output list"
    )
    args = parser.parse_args()

    input_list = args.input_list
    outfile = open(args.outfile, "w")

    with open(args.input_list) as list_of_files:
        files = list_of_files.readlines()
        for file in tqdm(files,
                         desc="Files processed",
                         total=len(files),
                         unit="file"):
            output = subprocess.check_output(["dirac-dms-lfn-replicas", file[:-1]])
            components = output.split(" ")
            disks = []
            for comp in components:
                if "Disk" in comp:
                    disks.append(comp)
            if any(disk in disks for disk in args.filter_disks):
                outfile.writelines(file)

    outfile.close()

if __name__ == "__main__":
    main()