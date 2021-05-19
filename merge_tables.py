#!/usr/bin/env python

import argparse
import glob
import logging

# PyTables
try:
    import tables as tb
except ImportError:
    logging.critical("Pytables is not installed in this environment (pip install tables).")


def merge_list_of_pytables(filename_list, destination):
    merged_tables = {}
    outfile = tb.open_file(destination, mode="w")
    all_previous_files_were_empty = True
    empty_files = 0

    for idx, filename in enumerate(sorted(filename_list)):
        
        logging.info("File # %d of %d" % (idx, len(filename_list)))
        logging.info("Filename %s" % filename)

        try:
            infile = tb.open_file(filename, mode="r")
        except tables.exceptions.HDF5ExtError:
            logging.warning('file %s appears to be corrupt' % filename)
            continue
            
        table_name_list = [table.name for table in infile.root]  # Name of tables
        
        if len(table_name_list) == 0:
            logging.warning('file %s appears to be empty' % filename)
            print 'file %s appears to be empty' % filename
            empty_file = True
            empty_files +=1
        else:
            empty_file = False

        # Initialise output file
        if (idx == 0) and not empty_file:
            logging.info("First file is not empty")
            for name in table_name_list:
                merged_tables[name] = infile.copy_node(
                    where="/", name=name, newparent=outfile.root
                )
            all_previous_files_were_empty = False
        elif all_previous_files_were_empty and (idx != 0) and not empty_file:
            logging.info("This is not the first file but is the first non-empty")
            for name in table_name_list:
                merged_tables[name] = infile.copy_node(
                    where="/", name=name, newparent=outfile.root
                )
            all_previous_files_were_empty = False
        elif all_previous_files_were_empty:
            logging.warning("Still no file with data...")
            print("Still no file with data...")
            infile.close()
            continue
        elif empty_file:
            logging.warning("Empty file! Closing and going to the next one...")
            print("Empty file! Closing and going to the next one...")
            infile.close()
            continue
        else:
            logging.info("File with data. Merging with the previous non-empty one...")
            for name in table_name_list:
                table_tmp = infile.get_node("/" + name)
                table_tmp.append_where(dstTable=merged_tables[name])

        infile.close()

    return merged_tables, empty_files


def main():
    parser = argparse.ArgumentParser(description="Merge collection of HDF5 files")
    parser.add_argument("--indir", type=str, default="./")
    parser.add_argument("--template_file_name", type=str, default="features_event")
    parser.add_argument("--outfile", type=str)
    args = parser.parse_args()

    print("DEBUG> template_file_name={}".format(args.template_file_name))
    print("DEBUG> indir={}".format(args.indir))
    print("DEBUG> outfile={}".format(args.outfile))

    input_template = "{}/{}*.h5".format(args.indir, args.template_file_name)
    print("input_template:", input_template)

    filename_list = glob.glob(input_template)
    print("filename_list (truncated):", filename_list[0:10])

    merged_tables, empty_files = merge_list_of_pytables(filename_list, args.outfile)
    
    if empty_files > 0:
        ratio = round(float(empty_files)/float(len(filename_list)), 2) * 100
        print "WARNING: %d over %f (%f%%) were empty!" % (empty_files, len(filename_list), ratio)


if __name__ == "__main__":

    main()
