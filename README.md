# GRID/DIRAC utilities
This repository contains scripts to deal with the GRID via the Dirac interface.
It contains utilities adapted from [here](https://github.com/tino-michael/tino_cta/tree/master/grid).

## Setup
In order to use those utilities you need: 
 - A working installation of Dirac (see the [CTA-DIRAC Users Guide](https://forge.in2p3.fr/projects/cta_dirac/wiki/CTA-DIRAC_Users_Guide))
 - The [PyYAML](https://pyyaml.org/) module (to handle configuration files)
 - The [HDF5](https://www.h5py.org/) module (to merge tables)
 - the [protopipe](https://drf-gitlab.cea.fr/CTA-Irfu/protopipe) module

Here is an example of environment variables bash file to activate the dirac settings:
```
#!/bin/bash
source $DIRAC_INSTALL_PATH/bashrc
dirac-proxy-init --legacy

export PROTOPIPE=$PYTOOLS/protopipe
export GRID=$PYTOOLS/grid
export PYWI=$PYTOOLS/pywi
export PYWICTA=$PYTOOLS/pywi-cta
```
where the DIRAC_INSTALL and PYTOOLS paths correspond respectively to the places
where you installed the dirac utilities and the protopipe and pywi-cta modules.

<aside class="warning">
Note that only Python 2.7 is supported for the scripts using Dirac utilities.
</aside>

## How to launch jobs on the GRID
The two test cases covered here are:
 - producing tables containing image parameters (and more) per type of camera to be
 further used for training of regressors (energy estimation) or classifiers
 (gamma/hadron separation)
 - production of DL2 event list, containing event parameter (direction, energy, score, etc.)

A single script called `submit_jobs.py` is used to submit jobs on the GRID and it uses
a configuration file based on YAML.

### Configuration file
The configuration file contains informations about:
 - The analysis through the configuration of the analysis, the type of the particle, etc.
 - The DIRAC parameters to launch jobs such as the output directory, the numbers of jobs, etc.
 - The list of simtel to be processed on the GRID (for gamma, electron and protons)   

Here is an example of a configuration file:
```
General:
 # Analysis configuration file (Need to be uploaded in the cloud)
 config_path: '/Users/julien/Documents/WorkingDir/Tools/python/protopipe/ana/prod_full_array_north_zen20_az0/configs/'
 config_file: 'ana.cfg'

 # Type of cleaning
 modes: ['tail']

 # Type for processing (gamma, proton, electron)
 particles: ['proton']

 # If true estimate energy (need regressor file)
 estimate_energy: True

 # Force the tailcut cleaning for energy/score estimation
 force_tailcut_for_extended_cleaning: False  # for reco and classify writer (evt level)

GRID:
 # Home on GRID
 home_grid: '/vo.cta.in2p3.fr/user/j/jlefaucheur/'

 # Output directories on the GRID home_grid/outdir
 outdir: 'cta/ana/'
 
 # home_grid/outdir/models
 model_dir: 'models'
 dl2_dir: 'dl2'

 # Number of file per job
 n_file_per_job: 1

 # Maximum number of jobs
 n_jobs_max: -1

EnergyRegressor:
 gamma_list: './list/Prod3b_NSB1x/LaPalma/gamma_energy.list'

GammaHadronClassifier:
 gamma_list: './list/Prod3b_NSB1x/LaPalma/gamma_classification.list'
 proton_list: './list/Prod3b_NSB1x/LaPalma/proton_classification.list'

Performance:
 gamma_list: './list/Prod3b_NSB1x/LaPalma/gamma_perf.list'
 proton_list: './list/Prod3b_NSB1x/LaPalma/proton_perf.list'
 electron_list: './list/Prod3b_NSB1x/LaPalma/electron_perf.list'
```

### How to produce tables for training
To launch the processing of events use the script `submit_jobs.py`:
```
$> python ./submit_jobs.py --help
usage: submit_jobs.py [-h] --config_file CONFIG_FILE [--max_events MAX_EVENTS]
                      [--test TEST] [--dry DRY] [--DL1 | --DL2]

Arguments for GRID submission

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
  --max_events MAX_EVENTS
                        maximum number of events considered per file
  --test TEST           Submit only one job
  --dry DRY             Do not submit any job
  --DL1                 if set, produce image tables
  --DL2                 if set, produce event tables
```
Here you should use the `DL1` options, images informations, along with event information,
will be saved in order to further train models.
INternally, the script `protopipe/scripts/write_dl1.py` is called.
Ine the configuration file, make sure to upload a regressor model on the GRID if you 
set the `estimate_energy` option to `True`.

### How to produce tables for performance estimation
To launch the processing of events use the script `submit_jobs.py`:
```
$> python ./submit_jobs.py --help
usage: submit_jobs.py [-h] --config_file CONFIG_FILE [--max_events MAX_EVENTS]
                      [--test TEST] [--dry DRY] [--DL1 | --DL2]

Arguments for GRID submission

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
  --max_events MAX_EVENTS
                        maximum number of events considered per file
  --test TEST           Submit only one job
  --dry DRY             Do not submit any job
  --DL1                 if set, produce image tables
  --DL2                 if set, produce event tables
```
Here you should use the `DL2` options to call the `protopipe/scripts/write_dl2.py` script.
Make sure to upload a regressor and a classifier model on the GRID in order to be able
to process entirely the events (energy and score estimation).

## Useful scripts
Here is a bunch of scripts wrapping DIRAC utilities.

### To merge multiple HDF5 tables
Tables are merged internally with the `./merge_tables.py` script:
```
$> python ./merge_tables.py --help
usage: merge_tables.py [-h] [--indir INDIR]
                       [--template_file_name TEMPLATE_FILE_NAME]
                       [--outfile OUTFILE]

Merge collection of HDF5 files

optional arguments:
  -h, --help            show this help message and exit
  --indir INDIR
  --template_file_name TEMPLATE_FILE_NAME
  --outfile OUTFILE
```

### To upload files on the GRID  
To upload a file one GRID use the `upload_file.py` script:
 ```
$> python ./upload_file.py --help
usage: upload_file.py [-h] [--indir INDIR] [--infile INFILE] [--outdir OUTDIR]

Upload collection files from Dirac

optional arguments:
  -h, --help       show this help message and exit
  --indir INDIR    Input repository
  --infile INFILE  Input file
  --outdir OUTDIR  Dirac repository
 ```

### To download files on the GRID  
To download a repository from the GRID use the `download_files.py` script:
 ```
$> python ./download_files.py --help
usage: download_files.py [-h] [--indir INDIR] [--outdir OUTDIR]

Download collection files from Dirac

optional arguments:
  -h, --help       show this help message and exit
  --indir INDIR    Dirac repository
  --outdir OUTDIR  Output file directory
 ```

### To delete a repository on the GRID  
To delete a repository from the GRID use the `download_files.py` script:
 ```
$> python ./delete_files.py --help
usage: delete_files.py [-h] [--indir INDIR]

Delete collection files from Dirac

optional arguments:
  -h, --help     show this help message and exit
  --indir INDIR  Dirac repository
```