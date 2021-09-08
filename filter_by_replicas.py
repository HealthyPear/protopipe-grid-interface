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
    parser.add_argument(
        "--max_files", type=int, default=None,
        help="Maximum number of files to scan"
    )
    args = parser.parse_args()

    input_list = args.input_list
    outfile = open(args.outfile, "w")

    with open(args.input_list) as list_of_lfns:
        lfns = list_of_lfns.readlines()[:args.max_files]
        for lfn in tqdm(lfns,
                         desc="Files processed",
                         total=len(files),
                         unit="file"):

            output = subprocess.check_output(["dirac-dms-lfn-replicas", lfn[:-1]])
            components = output.split(" ")

            disks = []
            for comp in components:
                if "Disk" in comp:
                    disks.append(comp)

            if ((len(args.filter_disks)==1) and (args.filter_disks == disks)):
                outfile.writelines(lfn)
            elif ((len(args.filter_disks)>1) and any(disk in disks for disk in args.filter_disks)):
                outfile.writelines(lfn)

    outfile.close()

if __name__ == "__main__":
    main()