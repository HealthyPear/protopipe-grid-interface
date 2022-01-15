# make 2 HDF5 files

import glob
import subprocess
from pkg_resources import resource_filename

import tables as tb


def create_mock_file(tmpdir, filename):

    filepath = tmpdir.join(filename)
    outfile = tb.open_file(filepath.strpath, mode="w", title="Run_1")

    cameras = ["NectarCam", "CHEC"]

    output_variables = dict(n=tb.Int16Col(dflt=-1, pos=0))

    outdata = {}
    out_table = {}
    for cam_id in cameras:
        if cam_id not in outdata:
            out_table[cam_id] = outfile.create_table(
                "/",
                cam_id,
                output_variables,
            )
            outdata[cam_id] = out_table[cam_id].row
        for n_image in range(50):
            outdata[cam_id]["n"] = 0
            outdata[cam_id].append()

    outfile.close()

    return None


def test_merge(tmpdir):

    print(tmpdir.strpath)

    # create 1st file
    create_mock_file(tmpdir, "run1.h5")
    # create 2nd file
    create_mock_file(tmpdir, "run2.h5")
    # define merged file
    merged_file_path = tmpdir.join("merged_file.h5").strpath

    # call script to merge
    subprocess.run(
        [
            "python",
            resource_filename("protopipe_grid_interface", "scripts/merge_tables.py"),
            "--indir",
            tmpdir.strpath,
            "--template_file_name",
            "*run*",
            "--outfile",
            merged_file_path,
        ],
        check=True,
    )

    cameras = ["NectarCam", "CHEC"]
    n_images_from_runs = dict.fromkeys(cameras, 0)
    n_tot_images = dict.fromkeys(cameras, 0)

    single_files = glob.glob("{}/*run*.h5".format(tmpdir.strpath))

    # Get total number of table rows cumulatively from each files per table
    for file in single_files:
        with tb.open_file(file, "r") as f:
            table_name_list = [table.name for table in f.root]
            assert sorted(table_name_list) == sorted(cameras)
            for child in f.root:
                n_images_from_runs[child._v_name] += len(child)

    # Get total number of table rows from merged file
    with tb.open_file(merged_file_path, "r") as f:
        for child in f.root:
            n_tot_images[child._v_name] = len(child)

    for camera in cameras:
        assert n_images_from_runs[camera] == n_tot_images[camera]
