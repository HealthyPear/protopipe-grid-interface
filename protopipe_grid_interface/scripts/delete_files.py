import argparse
import logging
import subprocess


def main():
    # Read command line options
    parser = argparse.ArgumentParser(
        description="Delete collection of files from Dirac folder"
    )
    parser.add_argument("--indir", default=None, help="Dirac repository")
    parser.add_argument("--log_level", default="INFO", help="Dirac repository")
    args = parser.parse_args()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logger.debug("Delete file from: %s", args.indir)

    # Get list of files
    batcmd = f"dirac-dms-user-lfns --BaseDir {args.indir}"
    result = subprocess.check_output(batcmd, shell=True)
    logger.debug(result)
    file_list = result.split()[-1]

    # Try reading the LFNs file
    try:
        with open(file_list, mode="r", encoding="utf8"):
            # Delete files
            batcmd = f"dirac-dms-remove-files {file_list}"
            result = subprocess.check_output(batcmd, shell=True)
    except IOError:
        logger.exception("Can't read LFNs file list.")

    # Final check
    # Get same list of files again
    batcmd = f"dirac-dms-user-lfns --BaseDir {args.indir}"
    result = subprocess.check_output(batcmd, shell=True)
    logger.debug(result)
    file_list = result.split()[-1]
    if len(file_list) > 0:
        logger.error("Some files appear to not be removed.")
    else:
        logger.info("Removal completed.")


if __name__ == "__main__":
    main()
