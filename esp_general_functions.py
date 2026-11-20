import os
import json

import numpy as np

def get_procdirs():

    pathdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "reference_info", "pathdirs.json")

    with open(pathdir, 'r') as f:
        pathdirs = json.load(f)

    return pathdirs

def get_deployment_info(deployment_name):

    """
    Load the deployment metadata dictionary for a specific deployment.
    
    Parameters:
    deployment_name (str): Name of the deployment to load metadata for.
    
    Returns:
    dict: Deployment metadata dictionary.
    """

    metadir = get_procdirs()['reference_info']
    metadata_filename = 'deployment_info.json'
    metadata_path = os.path.join(metadir, metadata_filename)

    with open(metadata_path, 'r') as f:
        deployment_info = json.load(f)

    if deployment_name not in deployment_info.keys():
        raise ValueError(f"Deployment '{deployment_name}' not found in metadata.")
    else:
        return deployment_info[deployment_name]

def detection_limit_flags(datavals):

    """
    Detections can be flagged by whether the flags are detectable and/or quantifiable. This function returns a dictionary of detection limit flags.

    Flag definitions:
    1: Quantifiable
    2: >=ULOQ
    3: LLOD<value<LLOQ
    4. <LLOD

    ULOQ: Upper Limit of Quantification
    LLOQ: Lower Limit of Quantification
    LLOD: Lower Limit of Detection
    """

    dataflags = []
    cleaned_vals = []

    for val in datavals:
        if val == '>ULOQ':
            dataflags.append(2)
            cleaned_vals.append(np.nan)
        elif val == '<LLOQ':
            dataflags.append(3)
            cleaned_vals.append(np.nan)
        elif val == '<LLOD':
            dataflags.append(4)
            cleaned_vals.append(np.nan)
        else:
            try:
                float_val = float(val)
                dataflags.append(1)
                cleaned_vals.append(float_val)
            except ValueError:
                # If the value cannot be converted to float, treat it as <LLOD
                dataflags.append(4)
                cleaned_vals.append(np.nan)

    return cleaned_vals, dataflags

