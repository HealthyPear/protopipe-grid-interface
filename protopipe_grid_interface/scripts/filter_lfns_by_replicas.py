__RCSID__ = "$Id$"

import sys
import argparse
from argparse import RawTextHelpFormatter
import logging
from multiprocessing import Pool
from functools import partial

from DIRAC.Core.Base import Script

Script.setUsageMessage(
    "\n".join(
        [
            "Filter a list of files by the disk(s) in which they have been replicated.",
            "python $GRID_INTERFACE/%s.py [options]" % Script.scriptName,
            "e.g.:",
            "python $GRID_INTERFACE/%s.py --analysis_path=shared_folder/analyses/test --output_type=DL2"
            % Script.scriptName,
        ]
    )
)

Script.registerSwitch("", "input_list=", "File containing a list of LFNs (required)")
Script.registerSwitch(
    "",
    "filter_disks=",
    "List of SEs in which to look for replicas (required; example --filter_disks CC-IN2P3-Disk DESY-ZN-Disk)",
)
Script.registerSwitch(
    "", "outfile=", "File where to store the selected LFNs (default: ./outfile.list)"
)
Script.registerSwitch(
    "", "max_files=", "Maximum number of LFN from input_list to scan (optional)"
)

Script.parseCommandLine()
switches = dict(Script.getUnprocessedSwitches())

if "input_list" not in switches:
    print("Input file list is missing: --input_list")
    sys.exit()
if "filter_disks" not in switches:
    print("List of SEs is missing: --filter_disks")
    sys.exit()
else:
    switches["filter_disks"] = [disk for disk in switches["filter_disks"].split(" ")]
if "outfile" not in switches:
    switches["outfile"] = "./outfile.list"
if "max_files" not in switches:
    switches["max_files"] = None
else:
    switches["max_files"] = int(switches["max_files"])

from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

fc = FileCatalog()


def getReplicas(lfn, disks):
    """Extract and write replicas from an LFN.

    Parameters
    ----------
    lfn: str
        String representing the full path of an LFN.
    disks: list
        List of SEs.
    outfile: file
        Output file where to save the selected LFNs.
    """

    res = fc.getReplicas(lfn)

    if not res["OK"]:
        logging.error(f"Error getting replicas for lfn: {lfn}")
        return res["Message"]

    if (
        (len(disks) == 1)
        and (len(res["Value"]["Successful"][lfn].keys()) == 1)
        and (disks[0] in res["Value"]["Successful"][lfn].keys())
    ):
        return lfn + "\n"
    elif (len(disks) > 1) and any(
        disk in res["Value"]["Successful"][lfn].keys() for disk in disks
    ):
        return lfn + "\n"


def main():

    outfile = open(switches["outfile"], "w")

    with open(switches["input_list"], "r") as input_file:

        infile_list = []
        for line in input_file:
            infile_list.append(line.rstrip())

        infile_list = infile_list[: switches["max_files"]]

        p = Pool(1)
        g = partial(getReplicas, disks=switches["filter_disks"])
        list_of_lfns = p.map(g, infile_list)

    result = [l for ll in list_of_lfns if ll is not None for l in ll]

    outfile = open(switches["outfile"], "w")
    for lfn in result:
        outfile.writelines(lfn)
    outfile.close()


if __name__ == "__main__":
    main()
