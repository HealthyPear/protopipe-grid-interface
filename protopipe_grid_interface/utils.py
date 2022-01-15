import logging
import logging.config
import os
from pkg_resources import resource_filename
import shutil
import subprocess
import yaml

from DIRAC.Interfaces.API.Dirac import Dirac

log = logging.getLogger(__name__)

DEFAULT_SE = "CC-IN2P3-USER"

__all__ = ["check_VOMS"]


class CustomFormatter(logging.Formatter):
    """Modify Formatter class to support ANSII colors."""

    def __init__(self, fmt=None, datefmt=None, style="%"):
        super(self.__class__, self).__init__()
        self.fmt = fmt
        self.datefmt = datefmt

        grey = "\x1b[38;20m"
        blue = "\x1b[34m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"

        format = self.fmt

        self.FORMATS = {
            logging.DEBUG: grey + format + reset,
            logging.INFO: blue + format + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        return formatter.format(record)


def initialize_logger(logger_name="default_logger", log_filename=None, append=True):
    """Initialize a logger using a default configuration."""
    # Get the default configuration file
    logging_configuration = resource_filename(
        "protopipe_grid_interface", "logging.yaml"
    )
    # Open it, load the configuration as a dictionary
    # Also allow for overriding of path and writing mode of the log file
    with open(logging_configuration) as file:
        loaded_config = yaml.safe_load(file)
        if log_filename is not None:
            loaded_config["handlers"]["file"]["filename"] = log_filename
        if append:
            loaded_config["handlers"]["file"]["mode"] = "a"
        logging.config.dictConfig(loaded_config)
    # Instantiate logger
    logger = logging.getLogger(logger_name)
    return logger


def check_VOMS():
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

            return None
    else:
        raise OSError(
            "Did not find voms-proxy-list executable: either install voms manually or using `conda install -c conda-forge voms`"
        )


def download(indir, outdir):
    """Upload a file to the grid using dirac-dms-add-file.

    Parameters
    ----------
    indir: str or pathlib.Path
        Input directory
    outdir: str or pathlib.Path
        Output directory
    """

    # Create output directory
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Get list of files
    batcmd = "dirac-dms-user-lfns --BaseDir {}".format(indir)
    result = subprocess.check_output(batcmd, shell=True)
    file_list = result.split()[-1]

    # try reading the lfns file
    try:
        grid_file_list = open(file_list)
    except IOError:
        raise IOError("cannot read lfns file list...")

    dirac = Dirac()

    file_collection = []
    for line in grid_file_list.read().splitlines():

        if len(file_collection) < 100:
            file_collection.append(line)  # files will be downloaded later
        else:
            dirac.getFile(file_collection, destDir=outdir)
            file_collection = []  # there won't be any loop at the end

    if file_collection:
        dirac.getFile(file_collection, destDir=outdir)

    return None


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
        log.error(f"Exit status: {e.returncode}")
        log.error(f"Command: {e.cmd}")
        log.error(f"STDOUT: {e.stdout}")
        log.error(f"STDERR: {e.stderr}")

    return None
