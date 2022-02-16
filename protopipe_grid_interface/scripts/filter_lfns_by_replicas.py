"""
Filter LFNs that have replicas onto a certain GRID location into a new file list.

Example:
  $ protopipe-FILTER-REPLICAS --input_list my_simtel_files.list --filter_disk CC-IN2P3-Disk --outfile filtered_files.list
"""
__RCSID__ = "$Id$"

import sys
import logging

from functools import partial
from tqdm.contrib.concurrent import process_map

from DIRAC.Core.Base import Script
from DIRAC.Resources.Catalog.FileCatalog import FileCatalog

Script.registerSwitch("", "input_list=", "File containing a list of LFNs (required)")
Script.registerSwitch(
    "",
    "filter_disks=",
    "List of SEs to scan (required; example --filter_disks [CC-IN2P3-Disk,DESY-ZN-Disk])",
)
Script.registerSwitch(
    "", "outfile=", "File where to store the selected LFNs (default: ./outfile.list)"
)
Script.registerSwitch(
    "", "max_files=", "Maximum number of LFN from input_list to scan (optional)"
)
Script.registerSwitch("", "n_cpu=", "Number of processes to use (default: 1)")
Script.registerSwitch("", "log_level=", "Logging level (default: INFO)")
Script.registerSwitch(
    "", "chunk_size=", "Size of chunks sent to worker processes (default: 1)"
)

Script.parseCommandLine()
switches = dict(Script.getUnprocessedSwitches())

if "input_list" not in switches:
    print("Input file list is missing: --input_list")
    sys.exit()
if "filter_disk" not in switches:
    print("List of SEs is missing: --filter_disk")
    sys.exit()
if "outfile" not in switches:
    switches["outfile"] = "./outfile.list"
if "max_files" not in switches:
    switches["max_files"] = None
else:
    switches["max_files"] = int(switches["max_files"])
if "n_cpu" not in switches:
    n_cpu = 1
else:
    switches["n_cpu"] = int(switches["n_cpu"])
if "chunk_size" not in switches:
    chunk_size = 1
else:
    switches["chunk_size"] = int(switches["chunk_size"])
if "log_level" not in switches:
    switches["log_level"] = "INFO"

fc = FileCatalog()


def get_replicas(lfn, disk, logger=None):
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

    logger.debug("Scanning replicas for LFN: %s", lfn)

    res = fc.getReplicas(lfn)

    if not res["OK"]:
        logger.error("Error getting replicas for lfn: %s", lfn)
        logger.error(res["Message"])
        return None

    successful = res["Value"]["Successful"]
    replicas = list(successful.values())[0]

    if disk not in replicas.keys():
        logger.debug("This LFN has no replicas in the disk that has been selected.")
        return None

    return lfn + "\n"


def main():

    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, switches["log_level"].upper()))

    logger.debug("Selected list of disks = %s", switches["filter_disks"])
    logger.debug("Opening input file %s...", switches["input_list"])
    with open(switches["input_list"], mode="r", encoding="utf8") as input_file:

        infile_list = []
        for line in input_file:
            infile_list.append(line.rstrip())

        logger.debug("Selecting first %i LFNs...", switches["max_files"])
        infile_list = infile_list[: switches["max_files"]]

        g = partial(get_replicas, disk=switches["filter_disk"], logger=logger)
        list_of_lfns = process_map(
            g,
            infile_list,
            max_workers=switches["n_cpu"],
            chunksize=switches["chunk_size"],
        )

    result = [lfn for lfn in list_of_lfns if lfn is not None]
    logger.debug("Got following list of LFNs:\n%s", result)

    logger.debug("Writing to output file %s...", switches["outfile"])
    with open(switches["outfile"], mode="w", encoding="utf8") as outfile:
        for lfn in result:
            outfile.writelines(lfn)


if __name__ == "__main__":
    main()
