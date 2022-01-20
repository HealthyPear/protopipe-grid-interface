import argparse
import glob
import logging
from pathlib import Path

try:
    import tables as tb
except ImportError:
    logging.critical(
        "Pytables is not installed in this environment (pip install tables)."
    )
from tqdm import tqdm

try:
    from protopipe_grid_interface.utils import initialize_logger

    initialize_default_logger = False
except ImportError:
    initialize_default_logger = True


def merge_call(template_file_name, indir, outfile, logger=None):

    logger.debug("template_file_name = %s", template_file_name)
    logger.debug("indir = %s", indir)
    logger.debug("outfile = %s", outfile)

    input_template = f"{indir}/{template_file_name}*.h5"
    logger.debug("input_template: %s", input_template)

    filename_list = glob.glob(input_template)
    logger.debug(f"filename_list (truncated to 10 files): {filename_list[0:10]}")

    _, empty_files = merge_list_of_pytables(filename_list, outfile, logger=logger)

    if empty_files > 0:
        ratio = round(float(empty_files) / float(len(filename_list)), 2) * 100
        logger.warning(
            "%d over %f (%f%%) were empty!", empty_files, len(filename_list), ratio
        )


def merge_list_of_pytables(filename_list, destination, logger=None):
    merged_tables = {}
    outfile = tb.open_file(destination, mode="w")
    all_previous_files_were_empty = True
    empty_files = 0

    for idx, filename in enumerate(tqdm(sorted(filename_list))):

        logger.debug("File # %d of %d", idx + 1, len(filename_list))
        logger.debug("Filename %s", filename)

        try:
            infile = tb.open_file(filename, mode="r")
        except tb.exceptions.HDF5ExtError:
            logger.warning("File %s appears to be corrupt", filename)
            continue

        table_name_list = [table.name for table in infile.root]  # Name of tables

        if len(table_name_list) == 0:
            logger.warning("file %s appears to be empty", filename)
            empty_file = True
            empty_files += 1
        else:
            empty_file = False

        # Initialise output file
        if (idx == 0) and not empty_file:
            logger.debug("First file is not empty")
            for name in table_name_list:
                merged_tables[name] = infile.copy_node(
                    where="/", name=name, newparent=outfile.root
                )
            all_previous_files_were_empty = False
        elif all_previous_files_were_empty and (idx != 0) and not empty_file:
            logger.debug("This is not the first file but is the first non-empty")
            for name in table_name_list:
                merged_tables[name] = infile.copy_node(
                    where="/", name=name, newparent=outfile.root
                )
            all_previous_files_were_empty = False
        elif all_previous_files_were_empty:
            logger.warning("Still no file with data...")
            infile.close()
            continue
        elif empty_file:
            logger.warning("Empty file! Closing and going to the next one...")
            infile.close()
            continue
        else:
            logger.debug("File with data. Merging with the previous non-empty one...")
            for name in table_name_list:
                table_tmp = infile.get_node("/" + name)
                table_tmp.append_where(dstTable=merged_tables[name])

        infile.close()
    outfile.close()

    return merged_tables, empty_files


def main():
    parser = argparse.ArgumentParser(description="Merge collection of HDF5 files")
    parser.add_argument("--indir", type=str, default="./")
    parser.add_argument("--template_file_name", type=str, default="features_event")
    parser.add_argument("--outfile", type=str)
    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help="""Override log file path
                (default: input directory)""",
    )
    args = parser.parse_args()

    if args.log_file is None:
        log_filepath = Path(args.indir) / "merge_tables.log"
    else:
        log_filepath = args.log_file
    if initialize_default_logger:
        log = logging.getLogger(__name__)
        log.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # add formatter to ch
        ch.setFormatter(formatter)
        # add ch to logger
        log.addHandler(ch)
    else:
        log = initialize_logger(
            logger_name=__name__, log_filename=log_filepath, append=False
        )

    merge_call(args.template_file_name, args.indir, args.outfile, logger=log)


if __name__ == "__main__":

    main()
