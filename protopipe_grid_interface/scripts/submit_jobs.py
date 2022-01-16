import os
import re
import datetime
import subprocess
import sys
from pathlib import Path
from pkg_resources import resource_filename

try:
    import protopipe

    protopipe_path = Path(protopipe.__path__[0])
except ImportError:
    raise ImportError("protopipe is not installed in this environment.") from None

from protopipe_grid_interface.utils import initialize_logger, load_config

try:
    from DIRAC.Core.Base import Script  # This allows to handle user arguments
except ImportError:
    error_message = """
    It seems that the tools necessary to use protopipe on DIRAC are not installed.
    Please use the environment.yaml file in the repository of this code.
    """
    raise ImportError(
        "You need dirac-grid installed to use this part of the interface"
    ) from None


Script.registerSwitch("", "analysis_path=", "Full path to the analysis folder")
Script.registerSwitch("", "output_type=", "Output data type (TRAINING or DL2)")
Script.registerSwitch(
    "", "max_events=", "Max number of events to be processed (optional, int)"
)
Script.registerSwitch("", "dry=", "If True do not submit job (default: False)")
Script.registerSwitch("", "test=", "If True submit only one job (default: False)")
Script.registerSwitch(
    "", "save_images=", "If True save images together with parameters (default: False)"
)

Script.registerSwitch(
    "",
    "debug_script=",
    "If True save debug information during execution of the script (default: False)",
)
Script.registerSwitch(
    "",
    "DataReprocessing=",
    "If True reprocess data from one site to another (default: False)",
)
Script.registerSwitch(
    "",
    "tag=",
    "Used only if DataReprocessing is True; only sites tagged with tag will be considered (default: None)",
)
Script.registerSwitch(
    "",
    "log_file=",
    "Override log file path (default: analysis.log in analysis folder)",
)
Script.parseCommandLine()
switches = dict(Script.getUnprocessedSwitches())

# These two imports need to stay here
from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac

# Control switches
if "analysis_path" not in switches:
    print("Analysis path argument is missing: --analysis_path")
    sys.exit()

if "output_type" not in switches:
    print("Output data level argument is missing: --output_type")
    sys.exit()

if "max_events" not in switches:
    switches["max_events"] = 10000000000
else:
    switches["max_events"] = int(switches["max_events"])

if "dry" not in switches:
    switches["dry"] = False
elif switches["dry"] in ["True", "true"]:
    switches["dry"] = True
else:
    switches["dry"] = False

if "test" not in switches:
    switches["test"] = False
elif switches["test"] in ["True", "true"]:
    switches["test"] = True
else:
    switches["test"] = False

if "save_images" not in switches:
    switches["save_images"] = False
elif switches["save_images"] in ["True", "true"]:
    switches["save_images"] = True
else:
    switches["save_images"] = False

if "debug_script" not in switches:
    switches["debug_script"] = False
elif switches["debug_script"] in ["True", "true"]:
    switches["debug_script"] = True
else:
    switches["debug_script"] = False

if "DataReprocessing" not in switches:
    switches["DataReprocessing"] = False
elif switches["DataReprocessing"] in ["True", "true"]:
    switches["DataReprocessing"] = True
else:
    switches["DataReprocessing"] = False

if "tag" not in switches:
    switches["tag"] = None
else:
    switches["tag"] = str(switches["tag"])

if "log_file" not in switches:
    switches["log_file"] = None
else:
    switches["log_file"] = str(switches["log_file"])


def main():

    # this thing pilots everything related to the GRID
    dirac = Dirac()

    # Check that analysis folder exists
    if not os.path.isdir(switches["analysis_path"]):
        raise ValueError(
            "This analysis folder doesn't exist yet - use create_analysis_tree.py"
        )

    # Initialize logger
    if switches["log_file"] is None:
        log_filepath = Path(switches["analysis_path"]) / "analysis.log"
        append = True
    else:
        log_filepath = switches["log_file"]
        append = False
    log = initialize_logger(
        logger_name=__name__, log_filename=log_filepath, append=append
    )

    if switches["output_type"] in "TRAINING":
        log.info("Preparing submission for TRAINING data")
    elif switches["output_type"] in "DL2":
        log.info("Preparing submission for DL2 data")
    else:
        log.critical("You have to choose either TRAINING or DL2 as output type!")
        sys.exit()

    # Initialize grid configuration
    cfg = load_config(os.path.join(switches["analysis_path"], "configs/grid.yaml"))

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
        log.debug("Force tail cuts for extended cleaning!!!")

    # Prepare command to launch script
    source_ctapipe = "source /cvmfs/cta.in2p3.fr/software/conda/dev/setupConda.sh"
    source_ctapipe += " && conda activate ctapipe_v0.11.0"

    if switches["output_type"] in "TRAINING":
        execute = "data_training.py"
        script_args = [
            f"--config_file={config_file}",
            f"--estimate_energy={str(estimate_energy)}",
            f"--regressor_config={regressor_method}.yaml",
            "--regressor_dir=./",
            "--outfile {outfile}",
            "--indir ./ --infile_list={infile_name}",
            f"--max_events={switches['max_events']}",
            "--{mode}",
            f"--cam_ids {cam_id_list}",
        ]
        output_filename_template = "TRAINING"
    elif switches["output_type"] in "DL2":
        execute = "write_dl2.py"
        script_args = [
            f"--config_file={config_file}",
            f"--regressor_config={regressor_method}.yaml",
            "--regressor_dir=./",
            f"--classifier_config={classifier_method}.yaml",
            "--classifier_dir=./",
            "--outfile {outfile}",
            "--indir ./ --infile_list={infile_name}",
            f"--max_events={switches['max_events']}",
            "--{mode}",
            "--force_tailcut_for_extended_cleaning={force_tailcut_for_extended_cleaning}",
            f"--cam_ids {cam_id_list}",
        ]
        output_filename_template = "DL2"

    # Make the script save also the full calibrated images if required
    if switches["save_images"] is True:
        script_args.append("--save_images")

    # Make the script print debug information if required
    if switches["debug_script"] is True:
        script_args.append("--debug")

    cmd = [source_ctapipe, "&&", "python " + execute]
    cmd += script_args

    pilot_args_write = " ".join(cmd)

    # For table merging if multiple runs
    pilot_args_merge = " ".join(
        [
            source_ctapipe,
            "&&",
            "python merge_tables.py",
            "--template_file_name",
            "{in_name}",
            "--outfile",
            "{out_name}",
        ]
    )

    prod3b_filelist = {}
    if estimate_energy is False and switches["output_type"] in "TRAINING":
        prod3b_filelist["gamma"] = cfg["EnergyRegressor"]["gamma_list"]
    elif estimate_energy is True and switches["output_type"] in "TRAINING":
        prod3b_filelist["gamma"] = cfg["GammaHadronClassifier"]["gamma_list"]
        prod3b_filelist["proton"] = cfg["GammaHadronClassifier"]["proton_list"]
    elif switches["output_type"] in "DL2":
        prod3b_filelist["gamma"] = cfg["Performance"]["gamma_list"]
        prod3b_filelist["proton"] = cfg["Performance"]["proton_list"]
        prod3b_filelist["electron"] = cfg["Performance"]["electron_list"]

    # Split list of files according to stoprage elements
    with open(prod3b_filelist[particle], mode="r", encoding="utf8") as f:
        filelist = f.readlines()

    filelist = ["{}".format(_.replace("\n", "")) for _ in filelist]
    res = dirac.splitInputData(filelist, n_file_per_job)
    list_run_to_loop_on = res["Value"]

    # define a template name for the file that's going to be written out.
    # the placeholder braces are going to get set during the file-loop
    output_filename = output_filename_template
    output_path = outdir
    if estimate_energy is False and switches["output_type"] in "TRAINING":
        output_path += f"/{training_dir_energy}/{particle}/"
        step = "energy"
    if estimate_energy is True and switches["output_type"] in "TRAINING":
        output_path += f"/{training_dir_classification}/{particle}/"
        step = "classification"
    if switches["output_type"] in "DL2":
        if force_tailcut_for_extended_cleaning is False:
            output_path += "/{dl2_dir}/{particle}/"
        else:
            output_path += f"/{dl2_dir}_force_tc_extended_cleaning/{particle}/"
        step = ""
    output_filename += "_{}.h5"

    # sets all the local files that are going to be uploaded with the job
    # plus the pickled classifier
    # if file name starts with `LFN:`, it will be copied from the GRID
    input_sandbox = [
        # Utility to assign one job to one command...
        resource_filename("protopipe_grid_interface", "aux/pilot.sh"),
        resource_filename("protopipe_grid_interface", "scripts/merge_tables.py"),
        os.path.expandvars(protopipe_path),
        os.path.expandvars(
            protopipe_path / f"scripts/{execute}"
        ),  # script that is being run
        os.path.expandvars(
            os.path.join(config_path, config_file)
        ),  # Configuration file
    ]

    models_to_upload = []
    configs_to_upload = []
    if estimate_energy is True and switches["output_type"] in "TRAINING":
        config_path_template = "LFN:" + os.path.join(
            home_grid, outdir, model_dir, "{}.yaml"
        )
        config_to_upload = config_path_template.format(regressor_method)
        configs_to_upload.append(config_to_upload)
        model_path_template = "LFN:" + os.path.join(
            home_grid, outdir, model_dir, "regressor_{}_{}.pkl.gz"
        )
        for cam_id in cam_id_list:

            model_to_upload = model_path_template.format(cam_id, regressor_method)
            models_to_upload.append(model_to_upload)
        log.debug("Model(s) to be uploaded to the GRID: \n%s", models_to_upload)
        log.debug(
            "Configuration file to be uploaded to the GRID: %s", configs_to_upload
        )

    elif estimate_energy is False and switches["output_type"] in "TRAINING":
        pass
    else:  # Charge also classifer for DL2
        model_type_list = ["regressor", "classifier"]
        model_method_list = [regressor_method, classifier_method]
        config_path_template = "LFN:" + os.path.join(
            home_grid, outdir, model_dir, "{}.yaml"
        )
        model_path_template = "LFN:" + os.path.join(
            home_grid, outdir, model_dir, "{}_{}_{}.pkl.gz"
        )
        if force_tailcut_for_extended_cleaning is True:
            force_mode = mode.replace("wave", "tail")
            log.debug("%s cleaning mode has been enforced", force_mode)
        else:
            force_mode = mode

        for idx, model_type in enumerate(model_type_list):

            config_to_upload = config_path_template.format(model_method_list[idx])
            configs_to_upload.append(config_to_upload)

            for cam_id in cam_id_list:

                if model_type in "regressor" and use_regressor is False:
                    log.debug("Do not upload regressor model on GRID!!!")
                    continue

                if model_type in "classifier" and use_classifier is False:
                    log.debug("Do not upload classifier model on GRID!!!")
                    continue

                model_to_upload = model_path_template.format(
                    model_type_list[idx], cam_id, model_method_list[idx]
                )

                models_to_upload.append(model_to_upload)
        log.debug(
            "Configuration files to be uploaded to the GRID: %s", configs_to_upload
        )
        log.debug("Model(s) to be uploaded to the GRID: \n%s", models_to_upload)

    # debug summary before submitting
    log.debug("Running command: %s", pilot_args_write)
    log.debug("Input sandbox: %s", input_sandbox)
    log.debug("Output file: %s", input_sandbox)
    log.debug("Particle type: %s", particle)
    log.debug("Energy estimation: %s", estimate_energy)

    # list of files on the GRID SE space
    # not submitting jobs where we already have the output
    batcmd = f"dirac-dms-user-lfns --BaseDir {os.path.join(home_grid, output_path)}"
    result = subprocess.check_output(batcmd, shell=True)
    try:
        with open(result.split()[-1], mode="r", encoding="utf8") as f:
            grid_filelist = f.readlines()
    except IOError:
        log.critical("Cannot read GRID filelist.", exc_info=True)

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
        log.debug("Scanning %s running/waiting jobs... please wait...", n_jobs)
        for i, job_id in enumerate(running_ids):
            if ((100 * i) / n_jobs) % 5 == 0:
                log.debug("\r%i %%", (((20 * i) / n_jobs) * 5))
            jobname = dirac.getJobAttributes(job_id)["Value"]["JobName"]
            running_names.append(jobname)

    n_jobs_remaining = n_jobs_max
    n_jobs_submitted = 0
    for n_job, bunch in enumerate(list_run_to_loop_on):

        log.info("JOB # %i", n_job + 1)

        # this selects the `runxxx` part of the first and last file in the run
        # list and joins them with a dash so that we get a nice identifier in
        # the output file name.
        # if there is only one file in the list, use only that one
        run_token = re.split("/", bunch[0])[-1].split("_")[3]
        if len(bunch) > 1:
            last_run = re.split("/", bunch[-1])[-1].split("_")[3]
            run_token = "-".join([run_token, last_run])

        # setting output name
        output_filenames = {}
        if switches["output_type"] in "DL2":
            job_name = f"protopipe_{config_name}_{switches['output_type']}_{particle}_{run_token}"
            output_filenames[mode] = output_filename.format(
                "_".join([particle, mode, run_token])
            )
        else:
            job_name = f"protopipe_{config_name}_{switches['output_type']}_{step}_{particle}_{run_token}"

            output_filenames[mode] = output_filename.format(
                "_".join([step, particle, mode, run_token])
            )

        # if job already running / waiting, skip
        if job_name in running_names:
            log.warning("%s still running", job_name)
            continue

        log.debug("Output file name: %s", output_filenames[mode])

        # if file already in GRID storage, skip
        # (you cannot overwrite it there, delete it and resubmit)
        # (assumes tail and wave will always be written out together)
        file_on_grid = os.path.join(output_path, output_filenames[mode])
        log.debug("Checking for existing file on GRID...")
        if file_on_grid in grid_filelist:
            log.warning(
                "The file associated to job %s is already stored on a GRID SE", job_name
            )
            continue

        if n_jobs_remaining == 0:
            log.warning("Maximum number of jobs to submit reached; breaking loop now")
            break

        j = Job()

        # runtime in seconds times 8 (CPU normalisation factor)
        j.setCPUTime(6 * 3600 * 8)
        j.setName(job_name)
        j.setInputSandbox(input_sandbox)

        if banned_sites:
            j.setBannedSites(banned_sites)

        # Add simtel files as input data
        j.setInputData(bunch)

        for i, run_file in enumerate(bunch):
            file_token = re.split("/", bunch[i])[-1].split("_")[3]

            # source the miniconda ctapipe environment and
            # run the python script with all its arguments
            if switches["output_type"] in "DL2":
                output_filename_temp = output_filename.format(
                    "_".join([particle, mode, file_token])
                )
            if switches["output_type"] in "TRAINING":
                output_filename_temp = output_filename.format(
                    "_".join([step, particle, mode, file_token])
                )

            j.setExecutable(
                "./pilot.sh",
                pilot_args_write.format(
                    outfile=output_filename_temp,
                    infile_name=os.path.basename(run_file),
                    mode=mode,
                ),
            )

            # check that the output file is there
            j.setExecutable(f"ls -lh {output_filename_temp}")

            # remove the current file to clear space
            j.setExecutable("rm", os.path.basename(run_file))

        # if there is more than one file per job, merge the output tables
        if len(bunch) > 1:
            names = []

            names.append(("*_{particle}_", output_filenames[mode]))

            for in_name, out_name in names:
                log.debug("in_name: %s, out_name: %s", in_name, out_name)
                j.setExecutable(
                    "./pilot.sh",
                    pilot_args_merge.format(in_name=in_name, out_name=out_name),
                )

                log.debug(
                    "args append: %s",
                    pilot_args_merge.format(in_name=in_name, out_name=out_name),
                )

        bunch.extend(models_to_upload)
        bunch.extend(configs_to_upload)
        j.setInputData(bunch)

        log.debug("Input data set to job = \n%s", bunch)

        outputs = []
        outputs.append(output_filenames[mode])
        log.debug(
            "Output file path from user's home: %s%s",
            output_path,
            output_filenames[mode],
        )

        j.setOutputData(outputs, outputSE=None, outputPath=output_path)

        # check if we should somehow stop doing what we are doing
        if switches["dry"] is True:
            log.info("This is a DRY RUN! -- NO job has been submitted!")
            log.info("Name of the job: %s", job_name)
            log.info("Name of the output file: %s", outputs)
            log.info("Output path from GRID home: %s", output_path)
            break

        # This allows to run the jobs sites different from where the input
        # data is located when the source site has been banned
        if switches["DataReprocessing"] is True:
            j.setType("DataReprocessing")
            if switches["tag"]:
                j.setTag(switches["tag"])
                log.debug(
                    "DataReprocessing has been activated with %s tag.", switches["tag"]
                )
            else:
                log.debug("DataReprocessing has been activated with no tag.")

        # this sends the job to the GRID and uploads all the
        # files into the input sandbox in the process
        log.info("SUBMITTING job with the following INPUT SANDBOX:\n %s", input_sandbox)
        log.info("Submission RESULT: %s", dirac.submitJob(j)["Value"])
        n_jobs_submitted += 1

        # break if this is only a test submission
        if switches["test"] is True:
            log.info("This is a TEST RUN! -- Only ONE job will be submitted!")
            log.info("Name of the job: %s", job_name)
            log.info("Name of the output file: %s", outputs)
            log.info("Output path from GRID home: %s", output_path)
            break

        # since there are two nested loops, need to break again
        if switches["test"] is True:
            break

    # Upload analysis configuration file for provenance

    se_list = ["CC-IN2P3-USER", "DESY-ZN-USER", "CNAF-USER", "CEA-USER"]
    analysis_config_local = os.path.join(config_path, config_file)
    # the configuration file is uploaded to the data directory because
    # the training samples (as well as their cleaning settings) are independent
    analysis_config_dirac = os.path.join(home_grid, output_path, config_file)

    if switches["dry"] is False:
        # Upload this file to all Dirac Storage Elements in SE_LIST
        for se in se_list:
            # the uploaded config file overwrites any old copy
            ana_cfg_upload_cmd = f"dirac-dms-add-file -f {analysis_config_dirac} {analysis_config_local} {se}"
            log.info(
                "Uploading %s to %s...", analysis_config_local, analysis_config_dirac
            )
            ana_cfg_upload_result = subprocess.run(
                ana_cfg_upload_cmd, shell=True, text=True, check=True
            )
            log.debug(ana_cfg_upload_result)
    else:
        log.info("This is a DRY RUN! -- analysis.yaml has NOT been uploaded.")

    n_jobs_planned = n_jobs_max if (n_jobs_max != -1) else len(list_run_to_loop_on)
    log.debug("%i job(s) have been planned", n_jobs_planned)
    log.info("%i job(s) have been submitted", n_jobs_submitted)


if __name__ == "__main__":
    main()
