import yaml
import argparse

def load_config(name):
    try:
        with open(name, 'r') as stream:
            cfg = yaml.load(stream)
    except IOError as e:
        print(e)
        raise
    return cfg


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def make_argparser():
    parser = argparse.ArgumentParser(description='Arguments for GRID submission')

    # Add configuration file
    parser.add_argument('--config_file', type=str, required=True)
    parser.add_argument('--max_events', type=int, default=100000000,
                        help="maximum number of events considered per file")
    parser.add_argument('--test', type=str2bool, default=False,
                        help="Submit only one job")
    parser.add_argument('--dry', type=str2bool, default=None,
                        help="Do not submit any job")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--DL1', dest="output_type", action='store_const',
                            const="DL1", default=None,
                            help="if set, produce image tables")
    mode_group.add_argument('--DL2', dest="output_type", action='store_const',
                            const="DL2", default=None,
                            help="if set, produce event tables")

    return parser