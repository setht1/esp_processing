#!/usr/bin/env python
# coding: utf-8

import os
import sys
import shutil
import argparse
from importlib import reload

import pandas as pd
import numpy as np
import datetime

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import netCDF4
from netCDF4 import Dataset

import esp_metadata as em

import esp_toxins as esp_tox


def esp_datawrapper(deployment, processing_type='all'):

    print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') +
          ' - Process deployment ' + deployment +
          ' (processing type: ' + processing_type + ')')

    if processing_type in ('toxin', 'all'):

        ##################
        # ESP Toxin Data #
        ##################


        esp_tox.processed_toxins_wrapper(deployment)

    if processing_type in ('hab', 'all'):

        ################
        # ESP HAB Data #
        ################

        pass

    return

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Process ESP data for a deployment into netCDF files.'
    )
    parser.add_argument(
        'deployment',
        help='Deployment name, for example 2025a.'
    )
    parser.add_argument(
        'processing_type',
        nargs='?',
        default='all',
        choices=['toxin', 'hab', 'all'],
        help='Type of data to process: toxin, hab, or all (default: all).'
    )
    return parser.parse_args(argv)


def main(argv=None):

    args = parse_args(argv)
    esp_datawrapper(args.deployment, args.processing_type)
    return 0

if __name__ == "__main__":
    sys.exit(main())

