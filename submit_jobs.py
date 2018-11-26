#!/usr/bin/env python
import os
import re
import random
import datetime
import subprocess
import sys

from DIRAC.Interfaces.API.Job import Job
from DIRAC.Interfaces.API.Dirac import Dirac

from utils import load_config, make_argparser


# bad sites
banned_sites = [
    'LCG.CPPM.fr',   # LFN connection problems
    #'LCG.IN2P3-CC.fr',  # jobs fail immediately after start
    'LCG.CIEMAT.es',  # GLIBC_2.14 not found
    'LCG.FRASCATI.it',  # GLIBC_2.14 not found
    'LCG.CYFRONET.pl',  # GLIBC_2.14 not found
    'ARC.SE-SNIC-T2.se',
    'LCG.CAMK.pl',      # no miniconda (bad vo configuration?)
    'LCG.Prague.cz',    # no miniconda (bad vo configuration?)
    'LCG.PRAGUE-CESNET.cz',    # no miniconda (bad vo configuration?)
    'LCG.OBSPM.fr',
    'LCG.LAPP.fr',      # no miniconda (bad vo configuration?)
    'LCG.PIC.es',       #
    'LCG.M3PEC.fr',     #
    'LCG.CETA.es',
    'LCG.DESY-ZEUTHEN.de',
    'LCG.GRIF.fr',
    'ARC.Prague.cz',
    'LCG.INFN-TORINO.it',
]


def sliding_window(my_list, window_size, step_size=None, start=0):

    step_size = step_size or window_size
    while start + window_size < len(my_list):
        yield my_list[start:start + window_size]
        start += step_size
    else:
        yield my_list[start:]


def main():
    """
    Launch job on the GRID
    """
    # Read arguments
    parser = make_argparser()
    args = parser.parse_args()

    if args.output_type is None:
        print('You have to choose DL1 or DL2 processing')
        sys.exit()
    elif args.output_type in 'DL1':
        print('Preparing submission for DL1 production')
    elif args.output_type in 'DL2':
        print('Preparing submission for DL2 production')
    else:
        print('You have to choose DL1 or DL2 processing')
        sys.exit()

    # Read configuration file
    cfg = load_config(args.config_file)

    # Analysis
    config_path = cfg['General']['config_path']
    config_file = cfg['General']['config_file']
    modes = cfg['General']['modes']
    particles = cfg['General']['particles']
    estimate_energy = cfg['General']['estimate_energy']
    force_tailcut_for_extended_cleaning = cfg['General']['force_tailcut_for_extended_cleaning']

    # Take parameters from the analysis configuration file
    config_name = load_config(os.path.join(config_path, config_file))['General']['config_name']
    print(config_name)
    cam_id_list = load_config(os.path.join(config_path, config_file))['General']['cam_id_list']

    # GRID
    outdir = os.path.join(cfg['GRID']['outdir'], config_name)
    n_file_per_job = cfg['GRID']['n_file_per_job']
    n_jobs_max = cfg['GRID']['n_jobs_max']
    model_dir = cfg['GRID']['model_dir']
    home_grid = cfg['GRID']['home_grid']

    # Prepare command to launch script
    source_ctapipe = 'source /cvmfs/cta.in2p3.fr/software/miniconda/bin/activate ctapipe_v0.6.1'
    if args.output_type in 'DL1':
        execute = 'write_dl1.py'
        script_args = ['--config_file={}'.format(config_file),
                       '--estimate_energy={}'.format(str(estimate_energy)),
                       '--regressor_dir=./',
                       '--outfile {outfile}',
                       '--indir ./ --infile_list *.simtel.gz',
                       '--max_events={}'.format(args.max_events),
                       '--{mode}',
                       '--cam_ids']
        output_filename_template = 'dl1'
    elif args.output_type in 'DL2':
        execute = 'write_dl2.py'
        script_args = ['--config_file={}'.format(config_file),
                       '--regressor_dir=./',
                       '--classifier_dir=./',
                       '--outfile {outfile}',
                       '--indir ./ --infile_list *.simtel.gz',
                       '--max_events={}'.format(args.max_events),
                       '--{mode}',
                       '--cam_ids']
        output_filename_template = 'dl2'
        args.estimate_energy = True

    cmd = [source_ctapipe, '&&', './' + execute]
    cmd += script_args

    pilot_args_write = ' '.join(cmd + cam_id_list)

    # For table merging if multiple runs
    pilot_args_merge = ' '.join([
        source_ctapipe, '&&',
        './merge_tables.py',
        '--template_file_name', '{in_name}',
        '--outfile', '{out_name}'])

    prod3b_filelist = dict()
    if estimate_energy is False and args.output_type in 'DL1':
        prod3b_filelist['gamma'] = open(cfg['EnergyRegressor']['gamma_list'])
    elif estimate_energy is True and args.output_type in 'DL1':
        prod3b_filelist['gamma'] = open(cfg['GammaHadronClassifier']['gamma_list'])
        prod3b_filelist['proton'] = open(cfg['GammaHadronClassifier']['proton_list'])
    elif args.output_type in 'DL2':
        prod3b_filelist['gamma'] = open(cfg['Performance']['gamma_list'])
        prod3b_filelist['proton'] = open(cfg['Performance']['proton_list'])
        prod3b_filelist['electron'] = open(cfg['Performance']['electron_list'])

    file_list_to_run_on = list()
    for part_id in particles:
        file_list_to_run_on.append(prod3b_filelist[part_id])

    # Number of files per job
    window_sizes = [n_file_per_job] * 3

    # I used the first few files to train the classifier and regressor -- skip them
    #start_runs = [50, 50, 0]
    # JLK, use dedicated list, should be removed without breaking things
    start_runs = [0, 0, 0]

    # define a template name for the file that's going to be written out.
    # the placeholder braces are going to get set during the file-loop
    output_filename = output_filename_template
    output_path = outdir
    if estimate_energy is False and args.output_type in 'DL1':
        output_path += '/energy/'
    if estimate_energy is True and args.output_type in 'DL1':
        output_path += '/discrimination/'
    if args.output_type in 'DL2':
        output_path += '/dl2/'
    output_filename += '_{}.h5'

    # sets all the local files that are going to be uploaded with the job plus the pickled
    # classifier (if the file name starts with `LFN:`, it will be copied from the GRID itself)
    input_sandbox = [
        # Utility to assign one job to one command...
        'pilot.sh',

        os.path.expandvars('$PROTOPIPE/protopipe/'),
        os.path.expandvars('./merge_tables.py'),

        # python wrapper for the mr_filter wavelet cleaning
        os.path.expandvars('$PYWI/pywi/'),
        os.path.expandvars('$PYWICTA/pywicta/'),
        './mr_filter',  # the executable for the wavelet cleaning

        # script that is being run
        os.path.expandvars('$PROTOPIPE/protopipe/scripts/' + execute),

        # Configuration file
        os.path.expandvars(os.path.join(config_path, config_file)),
    ]
    if estimate_energy is True and args.output_type in 'DL1':
        model_path_template = 'LFN:' + os.path.join(home_grid, outdir, model_dir, 'regressor_{}_{}_AdaBoostRegressor.pkl.gz')
        for cam_id in cam_id_list:
            for mode in modes:
                model_to_upload = model_path_template.format(mode, cam_id)
                print(model_to_upload)
                input_sandbox.append(model_to_upload)
    elif estimate_energy is False and args.output_type in 'DL1':
        pass
    else:  # Charge also classifer for DL2
        model_type_list = ['regressor', 'classifier']
        model_method_list = ['AdaBoostRegressor', 'AdaBoostClassifier']
        model_path_template = 'LFN:' + os.path.join(home_grid, outdir, model_dir, '{}_{}_{}_{}.pkl.gz')
        for idx, model_type in enumerate(model_type_list):
            for cam_id in cam_id_list:
                for mode in modes:
                    model_to_upload = model_path_template.format(
                        model_type_list[idx],
                        mode,
                        cam_id,
                        model_method_list[idx]
                    )
                    print(model_to_upload)
                    input_sandbox.append(model_to_upload)

    # summary before submitting
    print("\nDEBUG> running as:")
    print(pilot_args_write)
    print("\nDEBUG> with input_sandbox:")
    print(input_sandbox)
    print("\nDEBUG> with output file:")
    print(output_filename.format('{job_name}'))
    print("\nDEBUG> Particles:")
    print(particles)
    print("\nDEBUG> Energy estimation:")
    print(estimate_energy)

    # ########  ##     ## ##    ## ##    ## #### ##    ##  ######
    # ##     ## ##     ## ###   ## ###   ##  ##  ###   ## ##    ##
    # ##     ## ##     ## ####  ## ####  ##  ##  ####  ## ##
    # ########  ##     ## ## ## ## ## ## ##  ##  ## ## ## ##   ####
    # ##   ##   ##     ## ##  #### ##  ####  ##  ##  #### ##    ##
    # ##    ##  ##     ## ##   ### ##   ###  ##  ##   ### ##    ##
    # ##     ##  #######  ##    ## ##    ## #### ##    ##  ######

    # this thing submits all the jobs
    dirac = Dirac()

    # list of files on the GRID SE space
    # not submitting jobs where we already have the output
    batcmd = 'dirac-dms-user-lfns --BaseDir {}'.format(os.path.join(home_grid, output_path))
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
                [running_ids.add(id) for id in dirac.selectJobs(
                    status=status, date=day,
                    owner="jlefaucheur")['Value']]
            except KeyError:
                pass

    n_jobs = len(running_ids)
    if n_jobs > 0:
        print("getting names from {} running/waiting jobs... please wait..."
              .format(n_jobs))
        for i, id in enumerate(running_ids):
            if ((100 * i) / n_jobs) % 5 == 0:
                print("\r{} %".format(((20 * i) / n_jobs) * 5)),
            jobname = dirac.attributes(id)["Value"]["JobName"]
            running_names.append(jobname)
        else:
            print("\n... done")

    for i, filelist in enumerate(file_list_to_run_on):

        for run_filelist in sliding_window([l.strip() for l in filelist],
                                           window_sizes[i], start=start_runs[i]):

            if "gamma" in " ".join(run_filelist):
                channel = "gamma"
            elif "proton" in " ".join(run_filelist):
                channel = "proton"
            elif "electron" in " ".join(run_filelist):
                channel = "electron"
            else:
                print("not a known channel ... skipping this filelist:")
                break

            # this selects the `runxxx` part of the first and last file in the run
            # list and joins them with a dash so that we get a nice identifier in
            # the outpult file name. if there is only one file in the list, use only that one
            run_token = re.split('_', run_filelist[+0])[3]
            if len(run_filelist) > 1:
                run_token = '-'.join([run_token, re.split('_', run_filelist[-1])[3]])

            print("-" * 50)
            print("-" * 50)

            # setting output name
            job_name = '_'.join([channel, run_token])
            output_filenames = dict()
            for mode in modes:
                output_filenames[mode] = output_filename.format(
                    '_'.join([mode, channel, run_token]))

            # if job already running / waiting, skip
            if job_name in running_names:
                print("\n{} still running\n".format(job_name))
                continue

            print('Output file name: {}'.format(output_filenames[mode]))

            # if file already in GRID storage, skip
            # (you cannot overwrite it there, delete it and resubmit)
            # (assumes tail and wave will always be written out together)
            already_exist = False
            for mode in modes:
                file_on_grid = os.path.join(output_path, output_filenames[mode])
                print('DEBUG> check for existing file on GRID...')
                #print('file on grid: {}'.format(file_on_grid))
                #print('All files: {}'.format(grid_filelist))
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


            j = Job()  # WArning here :
            # 2018-10-22 15:00:21 UTC Framework ERROR: Problem retrieving sections in /Resources/Sites

            # runtime in seconds times 8 (CPU normalisation factor)
            j.setCPUTime(6 * 3600 * 8)
            j.setName(job_name)
            j.setInputSandbox(input_sandbox)

            if banned_sites:
                j.setBannedSites(banned_sites)

            # mr_filter loses its executable property by uploading it to the GRID SE; reset
            j.setExecutable('chmod', '+x mr_filter')
            j.setExecutable('ls -lah ./pywi/')
            j.setExecutable('ls -lah ./pywicta/')

            for run_file in run_filelist:
                file_token = re.split('_', run_file)[3]

                # wait for a random number of seconds (up to five minutes) before starting
                # to add a bit more entropy in the starting times of the dirac queries.
                # if too many jobs try in parallel to access the SEs, the interface crashes
                sleep = random.randint(0, 5 * 60)
                j.setExecutable('sleep', str(sleep))

                # consecutively downloads the data files, processes them, deletes the input
                # and goes on to the next input file; afterwards, the output files are merged
                j.setExecutable('dirac-dms-get-file', "LFN:" + run_file)

                # consecutively process file with wavelet and tailcut cleaning
                for mode in modes:
                    # source the miniconda ctapipe environment and run the python script with
                    # all its arguments
                    output_filename_temp = output_filename.format(
                        "_".join([mode, channel, file_token]))
                    j.setExecutable('./pilot.sh',
                                    pilot_args_write.format(
                                        outfile=output_filename_temp,
                                        mode=mode)
                                    )

                # remove the current file to clear space
                j.setExecutable('rm', os.path.basename(run_file))

            # simple `ls` for good measure
            j.setExecutable('ls', '-lh')

            # if there is more than one file per job, merge the output tables
            if window_sizes[i] > 1:
                names = []
                for mode in modes:
                    names.append((output_filename_template + '_' + mode, output_filenames[mode]))
                for in_name, out_name in names:
                    print('in_name: {}, out_name: {}'.format(in_name, out_name))
                    j.setExecutable('./pilot.sh',
                                    pilot_args_merge.format(
                                        in_name=in_name,
                                        out_name=out_name))

                    print('DEBUG> args append: {}'.format(
                        pilot_args_merge.format(
                            in_name=in_name,
                            out_name=out_name
                        )
                    ))

            outputs = []
            for mode in modes:
                outputs.append(output_filenames[mode])
                print("OutputData: {}{}".format(output_path, output_filenames[mode]))

            j.setOutputData(outputs,
                            outputSE=None, outputPath=output_path)

            # print(output_path)
            # print(output_filenames)
            # print('==> Check ok')
            # sys.exit()

            # check if we should somehow stop doing what we are doing
            if args.dry is True:
                print('\nrunning dry -- not submitting')
                print('outputs: {}'.format(outputs))
                print('output_path: {}'.format(output_path))
                break

            # this sends the job to the GRID and uploads all the
            # files into the input sandbox in the process
            print("\nsubmitting job")
            print(input_sandbox)
            print('Submission Result: {}\n'.format(dirac.submit(j)['Value']))

            # break if this is only a test submission
            if args.test is True:
                print("test run -- only submitting one job")
                break

        # since there are two nested loops, need to break again
        if args.dry is True or args.test is True:
            break

    try:
        os.remove("datapipe.tar.gz")
        os.remove("modules.tar.gz")
    except:
        pass

    print("\nall done -- exiting now")
    exit()


if __name__ == '__main__':
    main()
