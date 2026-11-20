import pandas as pd
import numpy as np
import datetime

import os

import esp_general_functions as esp
import esp_netcdf as esp_nc

def load_toxins_data(toxins_xls):
    """
    Load the toxins data from an Excel file and return it as a pandas DataFrame.
    
    Parameters:
    toxins_xls (str): Path to the Excel file containing toxins data.
    
    Returns:
    pd.DataFrame: DataFrame containing the toxins data.
    """
    if not os.path.exists(toxins_xls):
        raise FileNotFoundError(f"The specified toxins Excel file does not exist: {toxins_xls}")
    
    toxins_df = pd.read_excel(toxins_xls, engine='openpyxl')
    
    # Perform any necessary preprocessing on the DataFrame here
    # For example, converting date columns to datetime objects, handling missing values, etc.
    
    return toxins_df


def process_toxins_data(toxins_df):
    """
    Process the toxins DataFrame to extract relevant information and perform calculations.
    
    Parameters:
    toxins_df (pd.DataFrame): DataFrame containing the toxins data.
    
    Returns:
    pd.DataFrame: Processed DataFrame with additional calculations or filtered data.
    """

    # Convert all of the sample date columns to datetime objects
    date_columns = ['Sample start time', 'Sample end time',
                    'Auto exposure image timestamp',
                    'First fixed exposure image timestamp',
                    'Second fixed exposure image timestamp']
    for col in date_columns:
        if col in toxins_df.columns:
            toxins_df[col] = pd.to_datetime(toxins_df[col], errors='coerce')

    # Text columns are kept as they are
    string_columns = ['Deployment name',
                      'Auto exposure image filename',
                      'First fixed exposure image filename',
                      'Second fixed exposure image filename']

    # For all other columns, ensure that they are in the correct data type
    remaining_columns = [col for col in toxins_df.columns
                         if col not in date_columns and col not in string_columns]
    if 'Particulate domoic acid' in remaining_columns:
        remaining_columns.remove('Particulate domoic acid')
    for col in remaining_columns:
        toxins_df[col] = pd.to_numeric(toxins_df[col], errors='coerce')

    # Check the particulate demoic acid column for any flagged vales
    cleaned_vals, pdemo_flags = esp.detection_limit_flags(toxins_df['Particulate domoic acid'])
    toxins_df['Particulate domoic acid'] = cleaned_vals
    toxins_df['Particulate domoic acid flag'] = pdemo_flags

    return toxins_df



def processed_toxins_wrapper(deployment_name):

    """
    Wrapper function to load and process toxins data for a specific deployment.
    
    Parameters:
    deployment_name (str): Name of the deployment to process toxins data for.
    
    Returns:
    pd.DataFrame: Processed DataFrame containing toxins data for the specified deployment.
    """
    
    # Load the toxins data
    savedir = esp.get_procdirs()['datadir']
    toxin_filename = 'ERDDAPdeployment_toxin' + f"{deployment_name}.xlsx"
    toxins_xls = os.path.join(savedir, toxin_filename)
    
    toxins_df = load_toxins_data(toxins_xls)
    
    # Process the toxins data
    processed_toxins_df = process_toxins_data(toxins_df)

    # Load in the metadata dictionary for the deployment
    deployment_info = esp.get_deployment_info(deployment_name)

    # Write the processed toxins data to a new netCDF file
    
    esp_nc.make_esptoxins_netcdf(processed_toxins_df, deployment_name)
    return 