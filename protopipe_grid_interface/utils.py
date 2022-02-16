import logging
import logging.config
import os
from pkg_resources import resource_filename
import shutil
import subprocess
import yaml
from pathlib import Path

from DIRAC.Interfaces.API.Dirac import Dirac

log = logging.getLogger(__name__)

DEFAULT_SE = "CC-IN2P3-USER"


class CustomFormatter(logging.Formatter):
    """Modify Formatter class to support ANSII colors."""

    def __init__(self, fmt=None, datefmt=None, style="%"):
        """Initialize a standard Formatter color formatting."""
        super().__init__(fmt, datefmt, style)

        grey = "\x1b[38;20m"
        blue = "\x1b[34m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"

        if fmt is None:
            fmt = "%(message)s"
        if datefmt is None:
            datefmt = "%Y-%m-%d %H:%M:%S,uuu"

        self.FORMATS = {
            logging.DEBUG: grey + fmt + reset,
            logging.INFO: blue + fmt + reset,
            logging.WARNING: yellow + fmt + reset,
            logging.ERROR: red + fmt + reset,
            logging.CRITICAL: bold_red + fmt + reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)


def initialize_logger(
    logger_name="default_logger", conf=None, log_filename=None, append=True
):
    """Initialize a logger using a configuration file.

    Parameters
    ----------
    logger_name: str
        Name of the logger to use
        Default is "default_logger" from default config file specification
    conf: str or pathlib.Path
        Path to a custom configuration file
        Default is None, using the default config file
    log_filename: str
        Name of the log file to generate
        Default is None, using the default config file specification
    append: bool
        If to append logs to existing file
        Default is True

    Returns
    -------
    logger: logging.Logger
        Logger object

    """
    # Get the default configuration file
    if conf is None:
        logging_configuration = resource_filename(
            "protopipe_grid_interface", "aux/logging.yaml"
        )
    else:
        logging_configuration = conf
    # Open it, load the configuration as a dictionary
    # Also allow for overriding of path and writing mode of the log file
    with open(logging_configuration, mode="r", encoding="utf8") as file:
        loaded_config = yaml.safe_load(file)
        if log_filename is not None:
            loaded_config["handlers"]["file"]["filename"] = log_filename
        if append:
            loaded_config["handlers"]["file"]["mode"] = "a"
        logging.config.dictConfig(loaded_config)
    # Instantiate logger
    logger = logging.getLogger(logger_name)
    return logger


def check_voms():
    """Check that VOMS is initialized.

    The voms package doesn't seem to be a python package, so we check if the required command exists.
    If it exists we check the associated environment variables and set them if necessary.

    Returns
    -------
    voms_installed: bool
        True if the command exists in the environment.

    """

    if shutil.which("voms-proxy-list") is not None:

        env = os.environ

        if any(k not in env for k in ["X509_CERT_DIR", "X509_CERT_DIR", "X509_VOMSES"]):

            log.critical(
                """At least one of the environment variables X509_CERT_DIR, X509_CERT_DIR and X509_VOMSES are unset.
                   Please, review the usage instructions in the documentation"""
            )
    else:
        raise OSError(
            "Did not find voms-proxy-list executable: either install voms manually or using `conda install -c conda-forge voms`"
        )


def download(indir, outdir):
    """Download files from a user's folder on the GRID.

    Parameters
    ----------
    indir: str or pathlib.Path
        Input directory on the GRID
    outdir: str or pathlib.Path
        Output directory

    """

    # Create output directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Get list of files
    batcmd = f"dirac-dms-user-lfns --BaseDir {indir}"
    result = subprocess.check_output(batcmd, shell=True)
    file_list = result.split()[-1]

    # Open list and download each file
    try:
        with open(file_list, mode="r", encoding="utf8") as f:
            dirac = Dirac()

            file_collection = []
            for line in f.read().splitlines():

                if len(file_collection) < 100:
                    file_collection.append(line)  # files will be downloaded later
                else:
                    dirac.getFile(file_collection, destDir=outdir)
                    file_collection = []  # there won't be any loop at the end
            if file_collection:
                dirac.getFile(file_collection, destDir=outdir)
    except IOError:
        raise IOError("cannot read lfns file list...") from None


def upload(indir, infile, outdir, se=DEFAULT_SE):
    """Upload a file to the grid using dirac-dms-add-file.

    Parameters
    ----------
    indir: str or pathlib.Path
        Input directory
    infile: str
        Input file name
    outdir: str or pathlib.Path
        Output directory
    se: str
        Dirac Storage Element

    """

    file_to_upload = os.path.join(indir, infile)
    file_on_dirac = os.path.join(outdir, infile)

    try:
        result = subprocess.run(
            ["dirac-dms-add-file", file_on_dirac, file_to_upload, se],
            check=True,
            text=True,
            capture_output=True,
        )
        log.debug(result)
    except subprocess.CalledProcessError as e:
        log.error("Exit status: %s", e.returncode)
        log.error("Command: %s", e.cmd)
        log.error("STDOUT: %s", e.stdout)
        log.error("STDERR: %s", e.stderr)


def load_config(input_file):
    """Load a YAML configuration file.

    Parameters
    ----------
    input_file: str or pathlib.Path
        Path of the configuration file

    Returns
    -------
    cfg: object
        Python object (usually a dictionary).

    """
    try:
        with open(input_file, mode="r", encoding="utf8") as stream:
            cfg = yaml.safe_load(stream)
    except FileNotFoundError as e:
        raise e

    return cfg


def makedir(name, is_analysis=False, overwrite=False, logger=None):
    """Manage the creation of a new folder.

    Parameters
    ----------
    is_analysis: bool
        If True the directory is intended to be an analysis.
    overwrite: bool
        If True all contents will be removed at creation.
    name : pathlib.Path
        Folder to be created.
    result: int
        1 for success, 0 otherwise (any reason).

    """
    if (not name.exists()) or (name.exists() and overwrite):
        try:
            Path.mkdir(name, parents=True, exist_ok=True)
        except OSError as error:
            logger.exception(
                "Creation of the directory %s failed due to %s", name, error
            )
        else:
            logger.info(f"Successfully created the directory {name}")
    else:
        if is_analysis:
            additional_message = "(you can force it with ----overwrite-analysis)"
        else:
            additional_message = ""
        logger.warning(
            f"Directory {name} already exists and it won't be overwritten {additional_message}"
        )
