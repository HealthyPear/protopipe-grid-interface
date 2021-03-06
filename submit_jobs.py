#!/usr/bin/env python
import os
import re
import datetime
import subprocess
import sys
import yaml

# This allows to handle user arguments
from DIRAC.Core.Base import Script

# Set switches
Script.setUsageMessage(
    "\n".join(
        [
            "Usage:",
            "python %s [options]" % Script.scriptName,
            "e.g.:",
            "python %s --config_file=config.cfg --output_type=DL2" % Script.scriptName,
        ]
    )
)
Script.registerSwitch("", "config_file=", "Full path of configuration file")
Script.registerSwitch("", "output_type=", "Output data type (TRAINING or DL2)")
Script.registerSwitch(
    "", "max_events=", "Max number of events to be processed (optional, int)"
)
Script.registerSwitch("", "dry=", "If True do not submit job (default: False)")
Script.registerSwitch(
    "", "test=", "If True submit only one job (default: False)"
)
Script.registerSwitch(
    "", "save_images=", "If True save images together with parameters (default: False)"
)
Script.parseCommandLine()
switches = dict(Script.getUnprocessedSwitches())

# These two imports need to stay here
from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac

# Control switches
if switches.has_key("config_file") is False:
    print("Configuration file argument is missing: --config_file")
    sys.exit()

if switches.has_key("output_type") is False:
    print("Output data level argument is missing: --output_type")
    sys.exit()

if switches.has_key("max_events") is False:
    switches["max_events"] = 10000000000
else:
    switches["max_events"] = int(switches["max_events"])

if switches.has_key("dry") is False:
    switches["dry"] = False
elif switches["dry"] in ["True", "true"]:
    switches["dry"] = True
else:
    switches["dry"] = False

if switches.has_key("test") is False:
    switches["test"] = False
elif switches["test"] in ["True", "true"]:
    switches["test"] = True
else:
    switches["test"] = False

if switches.has_key("save_images") is False:
    switches["save_images"] = False
elif switches["save_images"] in ["True", "true"]:
    switches["save_images"] = True
else:
    switches["save_images"] = False


def load_config(name):
    try:
        with open(name, "r") as stream:
            cfg = yaml.load(stream)
    except FileNotFoundError as e:
        print(e)
        raise
    return cfg


def main():
    """
    Launch job on the GRID
    """
    # this thing pilots everything related to the GRID
    dirac = Dirac()

    if switches["output_type"] in "TRAINING":
        print("Preparing submission for TRAINING data")
    elif switches["output_type"] in "DL2":
        print("Preparing submission for DL2 data")
    else:
        print("You have to choose either TRAINING or DL2 as output type!")
        sys.exit()

    # Read configuration file
    cfg = load_config(switches["config_file"])

    # Analysis
    config_path = cfg["General"]["config_path"]
    config_file = cfg["General"]["config_file"]
    mode = cfg["General"]["mode"]  # One mode naw
    particle = cfg["General"]["particle"]
    estimate_energy = cfg["General"]["estimate_energy"]
    force_tailcut_for_extended_cleaning = cfg["General"][
        "force_tailcut_for_extended_cleaning"
    ]

    # Take parameters from the analysis configuration file
    ana_cfg = load_config(os.path.join(config_path, config_file))
    config_name = ana_cfg["General"]["config_name"]
    cam_id_list = ana_cfg["General"]["cam_id_list"]

    # Regressor and classifier methods
    regressor_method = ana_cfg["EnergyRegressor"]["method_name"]
    classifier_method = ana_cfg["GammaHadronClassifier"]["method_name"]

    # Someone might want to create DL2 without score or energy estimation
    if regressor_method in ["None", "none", None]:
        use_regressor = False
    else:
        use_regressor = True

    if classifier_method in ["None", "none", None]:
        use_classifier = False
    else:
        use_classifier = True

    # GRID
    outdir = os.path.join(cfg["GRID"]["outdir"], config_name)
    n_file_per_job = cfg["GRID"]["n_file_per_job"]
    n_jobs_max = cfg["GRID"]["n_jobs_max"]
    model_dir = cfg["GRID"]["model_dir"]
    training_dir_energy = cfg["GRID"]["training_dir_energy"]
    training_dir_classification = cfg["GRID"]["training_dir_classification"]
    dl2_dir = cfg["GRID"]["dl2_dir"]
    home_grid = cfg["GRID"]["home_grid"]
    user_name = cfg["GRID"]["user_name"]
    banned_sites = cfg["GRID"]["banned_sites"]

    # HACK
    if force_tailcut_for_extended_cleaning is True:
        print("Force tail cuts for extended cleaning!!!")

    # Prepare command to launch script
    source_ctapipe = "source /cvmfs/cta.in2p3.fr/software/conda/dev/setupConda.sh"
    source_ctapipe += " && conda activate ctapipe_v0.9.1"

    if switches["output_type"] in "TRAINING":
        execute = "data_training.py"
        script_args = [
            "--config_file={}".format(config_file),
            "--estimate_energy={}".format(str(estimate_energy)),
            "--regressor_dir=./",
            "--outfile {outfile}",
            "--indir ./ --infile_list={infile_name}",
            "--max_events={}".format(switches["max_events"]),
            "--{mode}",
            "--cam_ids {}".format(cam_id_list),
        ]
        output_filename_template = "TRAINING"
    elif switches["output_type"] in "DL2":
        execute = "write_dl2.py"
        script_args = [
            "--config_file={}".format(config_file),
            "--regressor_dir=./",
            "--classifier_dir=./",
            "--outfile {outfile}",
            "--indir ./ --infile_list={infile_name}",
            "--max_events={}".format(switches["max_events"]),
            "--{mode}",
            "--force_tailcut_for_extended_cleaning={}".format(
                force_tailcut_for_extended_cleaning
            ),
            "--cam_ids {}".format(cam_id_list),
        ]
        output_filename_template = "DL2"

    # Make the script save also the full calibrated images if required
    if switches["save_images"] is True:
        script_args.append("--save_images")

    cmd = [source_ctapipe, "&&", "./" + execute]
    cmd += script_args

    pilot_args_write = " ".join(cmd)

    # For table merging if multiple runs
    pilot_args_merge = " ".join(
        [
            source_ctapipe,
            "&&",
            "./merge_tables.py",
            "--template_file_name",
            "{in_name}",
            "--outfile",
            "{out_name}",
        ]
    )

    prod3b_filelist = dict()
    if estimate_energy is False and switches["output_type"] in "TRAINING":
        prod3b_filelist["gamma"] = cfg["EnergyRegressor"]["gamma_list"]
    elif estimate_energy is True and switches["output_type"] in "TRAINING":
        prod3b_filelist["gamma"] = cfg["GammaHadronClassifier"]["gamma_list"]
        prod3b_filelist["proton"] = cfg["GammaHadronClassifier"]["proton_list"]
    elif switches["output_type"] in "DL2":
        prod3b_filelist["gamma"] = cfg["Performance"]["gamma_list"]
        prod3b_filelist["proton"] = cfg["Performance"]["proton_list"]
        prod3b_filelist["electron"] = cfg["Performance"]["electron_list"]

    # from IPython import embed
    # embed()

    # Split list of files according to stoprage elements
    with open(prod3b_filelist[particle]) as f:
        filelist = f.readlines()

    filelist = ["{}".format(_.replace("\n", "")) for _ in filelist]
    res = dirac.splitInputData(filelist, n_file_per_job)
    list_run_to_loop_on = res["Value"]

    # define a template name for the file that's going to be written out.
    # the placeholder braces are going to get set during the file-loop
    output_filename = output_filename_template
    output_path = outdir
    if estimate_energy is False and switches["output_type"] in "TRAINING":
        output_path += "/{}/".format(training_dir_energy)
        step = "energy"
    if estimate_energy is True and switches["output_type"] in "TRAINING":
        output_path += "/{}/".format(training_dir_classification)
        step = "classification"
    if switches["output_type"] in "DL2":
        if force_tailcut_for_extended_cleaning is False:
            output_path += "/{}/".format(dl2_dir)
        else:
            output_path += "/{}_force_tc_extended_cleaning/".format(dl2_dir)
        step = ""
    output_filename += "_{}.h5"

    # sets all the local files that are going to be uploaded with the job
    # plus the pickled classifier
    # if file name starts with `LFN:`, it will be copied from the GRID
    input_sandbox = [
        # Utility to assign one job to one command...
        os.path.expandvars("$GRID/pilot.sh"),
        os.path.expandvars("$PROTOPIPE/protopipe/"),
        os.path.expandvars("$GRID/merge_tables.py"),
        # python wrapper for the mr_filter wavelet cleaning
        # os.path.expandvars("$PYWI/pywi/"),
        # os.path.expandvars("$PYWICTA/pywicta/"),
        # script that is being run
        os.path.expandvars("$PROTOPIPE/protopipe/scripts/" + execute),
        # Configuration file
        os.path.expandvars(os.path.join(config_path, config_file)),
    ]

    models_to_upload = []
    if estimate_energy is True and switches["output_type"] in "TRAINING":
        model_path_template = "LFN:" + os.path.join(
            home_grid, outdir, model_dir, "regressor_{}_{}_{}.pkl.gz"
        )
        for cam_id in cam_id_list:
            model_to_upload = model_path_template.format(
                mode, cam_id, regressor_method
            )  # TBC
            print("The following model(s) will be uploaded to the GRID:")
            print(model_to_upload)
            models_to_upload.append(model_to_upload)
            # input_sandbox.append(model_to_upload)
    elif estimate_energy is False and switches["output_type"] in "TRAINING":
        pass
    else:  # Charge also classifer for DL2
        model_type_list = ["regressor", "classifier"]
        model_method_list = [regressor_method, classifier_method]
        model_path_template = "LFN:" + os.path.join(
            home_grid, outdir, model_dir, "{}_{}_{}_{}.pkl.gz"
        )
        if force_tailcut_for_extended_cleaning is True:
            force_mode = mode.replace("wave", "tail")
            print("################")
            print(force_mode)
        else:
            force_mode = mode
        for idx, model_type in enumerate(model_type_list):
            for cam_id in cam_id_list:

                if model_type in "regressor" and use_regressor is False:
                    print("Do not upload regressor model on GRID!!!")
                    continue

                if model_type in "classifier" and use_classifier is False:
                    print("Do not upload classifier model on GRID!!!")
                    continue

                model_to_upload = model_path_template.format(
                    model_type_list[idx],
                    force_mode,
                    cam_id,
                    model_method_list[idx]
                )
                print("The following model(s) will be uploaded to the GRID:")
                print(model_to_upload)
                models_to_upload.append(model_to_upload)
                # input_sandbox.append(model_to_upload)

    # summary before submitting
    print("\nDEBUG> running as:")
    print(pilot_args_write)
    print("\nDEBUG> with input_sandbox:")
    print(input_sandbox)
    print("\nDEBUG> with output file:")
    print(output_filename.format("{job_name}"))
    print("\nDEBUG> Particles:")
    print(particle)
    print("\nDEBUG> Energy estimation:")
    print(estimate_energy)

    # ########  ##     ## ##    ## ##    ## #### ##    ##  ######
    # ##     ## ##     ## ###   ## ###   ##  ##  ###   ## ##    ##
    # ##     ## ##     ## ####  ## ####  ##  ##  ####  ## ##
    # ########  ##     ## ## ## ## ## ## ##  ##  ## ## ## ##   ####
    # ##   ##   ##     ## ##  #### ##  ####  ##  ##  #### ##    ##
    # ##    ##  ##     ## ##   ### ##   ###  ##  ##   ### ##    ##
    # ##     ##  #######  ##    ## ##    ## #### ##    ##  ######

    # list of files on the GRID SE space
    # not submitting jobs where we already have the output
    batcmd = "dirac-dms-user-lfns --BaseDir {}".format(
        os.path.join(home_grid, output_path)
    )
    result = subprocess.check_output(batcmd, shell=True)
    try:
        grid_filelist = open(result.split()[-1]).read()
    except IOError:
        raise IOError("cannot read GRID filelist...")

    # get jobs from today and yesterday...
    days = []
    for i in range(2):  # how many days do you want to look back?
        days.append((datetime.date.today() - datetime.timedelta(days=i)).isoformat())

    # get list of run_tokens that are currently running / waiting
    running_ids = set()
    running_names = []
    for status in ["Waiting", "Running", "Checking"]:
        for day in days:
            try:
                [
                    running_ids.add(id)
                    for id in dirac.selectJobs(
                        status=status, date=day, owner=user_name
                    )["Value"]
                ]
            except KeyError:
                pass

    n_jobs = len(running_ids)
    if n_jobs > 0:
        print(
            "Scanning {} running/waiting jobs... please wait...".format(
                n_jobs
            )
        )
        for i, id in enumerate(running_ids):
            if ((100 * i) / n_jobs) % 5 == 0:
                print("\r{} %".format(((20 * i) / n_jobs) * 5)),
            jobname = dirac.getJobAttributes(id)["Value"]["JobName"]
            running_names.append(jobname)
        else:
            print("\n... done")

    for bunch in list_run_to_loop_on:

        # for bunch in bunches_of_run:

        # from IPython import embed
        # embed()

        # this selects the `runxxx` part of the first and last file in the run
        # list and joins them with a dash so that we get a nice identifier in
        # the output file name.
        # if there is only one file in the list, use only that one
        # run_token = re.split('_', bunch[+0])[3]  # JLK JLK
        run_token = re.split("_", bunch[0])[3]
        if len(bunch) > 1:
            run_token = "-".join([run_token, re.split("_", bunch[-1])[3]])

        print("-" * 50)
        print("-" * 50)

        # setting output name
        output_filenames = dict()
        if switches["output_type"] in "DL2":
            job_name = "protopipe_{}_{}_{}_{}_{}".format(config_name,
                                               switches["output_type"],
                                               particle,
                                               run_token,
                                               mode)
            output_filenames[mode] = output_filename.format(
                "_".join([particle, mode, run_token])
            )
        else:
            job_name = "protopipe_{}_{}_{}_{}_{}_{}".format(config_name,
                                                  switches["output_type"],
                                                  step,
                                                  particle,
                                                  run_token,
                                                  mode)
            output_filenames[mode] = output_filename.format(
                "_".join([step, particle, mode, run_token])
            )

        # if job already running / waiting, skip
        if job_name in running_names:
            print("\n{} still running\n".format(job_name))
            continue

        print("Output file name: {}".format(output_filenames[mode]))

        # if file already in GRID storage, skip
        # (you cannot overwrite it there, delete it and resubmit)
        # (assumes tail and wave will always be written out together)
        already_exist = False
        file_on_grid = os.path.join(output_path, output_filenames[mode])
        print("DEBUG> check for existing file on GRID...")
        if file_on_grid in grid_filelist:
            print("\n{} already on GRID SE\n".format(job_name))
            already_exist = True
            break
        if already_exist is True:
            continue

        if n_jobs_max == 0:
            print("maximum number of jobs to submit reached")
            print("breaking loop now")
            break
        else:
            n_jobs_max -= 1

        j = Job()

        # runtime in seconds times 8 (CPU normalisation factor)
        j.setCPUTime(6 * 3600 * 8)
        j.setName(job_name)
        j.setInputSandbox(input_sandbox)

        if banned_sites:
            j.setBannedSites(banned_sites)

        # Add simtel files as input data
        j.setInputData(bunch)

        for run_file in bunch:
            file_token = re.split("_", run_file)[3]

            # wait for a random number of seconds (up to five minutes) before
            # starting to add a bit more entropy in the starting times of the
            # dirac queries.
            # if too many jobs try in parallel to access the SEs,
            # the interface crashes
            # #sleep = random.randint(0, 20)  # seconds
            # #j.setExecutable('sleep', str(sleep))

            # JLK: Try to stop doing that
            # consecutively downloads the data files, processes them,
            # deletes the input
            # and goes on to the next input file;
            # afterwards, the output files are merged
            # j.setExecutable('dirac-dms-get-file', "LFN:" + run_file)

            # source the miniconda ctapipe environment and
            # run the python script with all its arguments
            output_filename_temp = output_filename.format(
                "_".join([mode, particle, file_token])
            )
            j.setExecutable(
                "./pilot.sh",
                pilot_args_write.format(
                    outfile=output_filename_temp,
                    infile_name=os.path.basename(run_file),
                    mode=mode,
                ),
            )

            # remove the current file to clear space
            j.setExecutable("rm", os.path.basename(run_file))

        # simple `ls` for good measure
        j.setExecutable("ls", "-lh")

        # if there is more than one file per job, merge the output tables
        if len(bunch) > 1:
            names = []
            names.append(
                (output_filename_template + "_" + mode, output_filenames[mode])
            )
            for in_name, out_name in names:
                print("in_name: {}, out_name: {}".format(in_name, out_name))
                j.setExecutable(
                    "./pilot.sh",
                    pilot_args_merge.format(in_name=in_name, out_name=out_name),
                )

                print(
                    "DEBUG> args append: {}".format(
                        pilot_args_merge.format(in_name=in_name, out_name=out_name)
                    )
                )

        bunch.extend(models_to_upload)
        j.setInputData(bunch)

        print("Input data set to job = {}".format(bunch))

        outputs = []
        outputs.append(output_filenames[mode])
        print("Output file path: {}{}".format(output_path, output_filenames[mode]))

        j.setOutputData(outputs, outputSE=None, outputPath=output_path)

        # check if we should somehow stop doing what we are doing
        if switches["dry"] is True:
            print("\nThis is a dry run! -- No job has been submitted!")
            print("Name of the job: {}".format(job_name))
            print("Name of the output file: {}".format(outputs))
            print("Output pah from GRID home: {}".format(output_path))
            break

        # this sends the job to the GRID and uploads all the
        # files into the input sandbox in the process
        print("\nsubmitting job")
        print(input_sandbox)
        print("Submission Result: {}\n".format(dirac.submitJob(j)["Value"]))

        # break if this is only a test submission
        if switches["test"] is True:
            print("This is a test run! -- Only one job will be submitted!")
            print("Name of the job: {}".format(job_name))
            print("Name of the output file: {}".format(outputs))
            print("Output pah from GRID home: {}".format(output_path))
            break

        # since there are two nested loops, need to break again
        if switches["test"] is True:
            break

    try:
        os.remove("datapipe.tar.gz")
        os.remove("modules.tar.gz")
    except:
        pass

    print("\nall done -- exiting now")
    exit()


if __name__ == "__main__":
    main()
