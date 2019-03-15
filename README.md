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
 further used for the training of regressors (energy estimation) or classifiers
 (gamma/hadron separation)
 - production of DL2 event list, containing event parameter (direction, energy, score, etc.)

A single script called `submit_jobs_new_scheme.py` is used to submit jobs on the GRID and it uses
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
 particle: 'proton'

 # If true estimate energy (need regressor file)
 estimate_energy: True

 # Force the tailcut cleaning for energy/score estimation
 force_tailcut_for_extended_cleaning: False  # for reco and classify writer (evt level)

GRID:
 # User name
 user_name: 'jlefaucheur'

 # Home on GRID
 home_grid: '/vo.cta.in2p3.fr/user/j/jlefaucheur/'

 # Output directories on the GRID home_grid/outdir
 outdir: 'cta/ana/'

 # Directory for DL1
 dl1_dir_energy: 'new_dl1_energy'

 # Directory for DL1
 dl1_dir_discrimination: 'new_dl1_discrimination'

 # home_grid/outdir/models
 model_dir: 'new_models'

 # Directory for DL2
 dl2_dir: 'new_dl2'

 # Number of file per job
 n_file_per_job: 1

 # Maximum number of jobs
 n_jobs_max: -1
 
 # Banned sites
 banned_sites: ['LCG.CPPM.fr']  # Badly configure

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

### How to get a list of Monte-Carlo files
A bunch of tools related to CTA is provided with the dirac installation
to get information about the existing Monte-Carlo productions and to retrieve the
simulated data. Two importants tools are needed.

The first tool is `cta-prod3-show-dataset` which allow a user to get all the information
about the corresponding dataset:
```
$> cta-prod3-show-dataset --help

Get PROD3 statistics for a given dataset
if no dataset is specified it gives the list of available datasets
Usage:
   cta-prod3-show-dataset <dataset>
```
If a production name is given it will show the characteristics of the production. 
If no production name is given all of them will be shown.

The second tool is used to retrieve the list of files, on the GRID, corresponding to 
one Monte-Carlo production:
```
$> cta-prod3-dump-dataset --help

Dump in a file the list of PROD3 files for a given dataset

Usage:
   cta-prod3-dump-dataset <dataset> 
```
The file list will be saved on disk.

Up to now, we have focused on the MC production labelled as `NSB1x` since they contain 
the 'final' subarrays and are thus easier to process than the official productions (which
contain a lot of telescopes, e.g. 400).


### How to produce tables for training
To launch the processing of events use the script `submit_jobs_new_scheme.py`:
```
$> python ./submit_jobs_new_scheme.py --help

Usage:
python submit_jobs_new_scheme [options]
e.g.:
python submit_jobs_new_scheme --config_file=config.cfg --output_type=DL1

Options:
  -   --config_file=           : Configuration file
  -   --output_type=           : Data level output, e.g. DL1 or DL2, str
  -   --max_events=            : Maximal number of events to be processed, int, optional
  -   --dry=                   : If in [True, true] do not submit job, str, optional
  -   --test=                  : If in [True, true] submit only one job, str, optional
```
Here you should use the `--output_type=DL1` options, images information, 
along with event information, will be saved in order to further train models.
Internally, the script `protopipe/scripts/write_dl1.py` is called.
Depending whether you want to build tables to train an energy estimator or a classifier, 
you will need to specify the lists containing the MC files in `EnergyRegressor` and 
`GammaHadronClassifier` sections, respectively, of the configuration file.

**Make sure to upload a regressor model on the GRID if you 
set the `estimate_energy` option to `True` in the configuration file 
in order to build tables to train a classifier.**
This is something that could be improve.

### How to produce tables for performance estimation
To launch the processing of events use the script `submit_jobs_new_scheme.py`:
```
$> python ./submit_jobs_new_scheme.py --help

Usage:
python submit_jobs_new_scheme [options]
e.g.:
python submit_jobs_new_scheme --config_file=config.cfg --output_type=DL2

Options:
  -   --config_file=           : Configuration file
  -   --output_type=           : Data level output, e.g. DL1 or DL2, str
  -   --max_events=            : Maximal number of events to be processed, int, optional
  -   --dry=                   : If in [True, true] do not submit job, str, optional
  -   --test=                  : If in [True, true] submit only one job, str, optional
```
Here you should use the `--output_type=DL2` options to call the 
`protopipe/scripts/write_dl2.py` script.
You will need to specify the list of MC files for the gamma, proton and electron in the 
section `Performance`.

**Make sure to upload a regressor and a classifier model on the GRID in order to be able
to fully process the events (energy and gammaness/score estimation).**

**If you want to generate DL2 tables without the estimation of the energy or the score, you
will need to specify `None` as attributs for the machine learning methods
in the analysis configuration (`EnergyRegressor` and `GammaHadronClassifier` sections)
used by `protopipe/scripts/write_dl2.py`.** 


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

## Useful tips 

### Make replicates of permanent files
For permanent files you should make replicates in order to avoid to saturate the
storage elements. This is particularly important for regression or classification
model. In order to make a replicate you should do:
```
$> dirac-dms-replicate-lfn the_file_on_grid the_storage_element
```
Here is a list of some storage elements:
* CC-IN2P3-USER
* DESY-ZN-USER
* CNAF-USER
* CEA-USER (badly configured, apparently)
* LAPP-USER

### SSLError by using pip
Try to add the following options:
```
--trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org
```

### Zeuthen storage
At this time the DESY-ZN-Disk storage element is badly configured
and you should add the following lines in the etc/dirac.cfg
configuration file (in your DIRAC install):
```
Resources
{
  StorageElements
  {
    DESY-ZN-Disk
    {
      AccessProtocol.1
      {
      Access = remote
      PluginName = GFAL2_SRM2
      Host = globe-door.ifh.de
      Port = 8443
      Protocol = srm
      Path = /pnfs/ifh.de/acs/grid/cta
      SpaceToken =
      WSUrl = /srm/managerv2?SFN=
      ProtocolsList = file
      }
    }
  }
}
```