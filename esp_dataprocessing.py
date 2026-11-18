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


# # Google API Access

# In[ ]:


def googleapi_get_user_token():

    """
    Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """

    creds = None
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive.readonly",
              "https://www.googleapis.com/auth/drive.file",
              "https://www.googleapis.com/auth/drive"]

    curdir = os.getcwd()
    if '/hdd0/orca/' in curdir:
        auth_dir = '/hdd0/orca/orca_python/tokens/'
    else:
        auth_dir = 'C:/Users/APLUser/NEMO_Data/ESP_Processing/tokens'

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(os.path.join(auth_dir, 'token.json')):
        creds = Credentials.from_authorized_user_file(os.path.join(auth_dir, 'token.json'), SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(auth_dir, 'esp_pnw_oauth.json'), SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(os.path.join(auth_dir, 'token.json'), "w") as token:
            token.write(creds.to_json())

    return


# In[ ]:


def googleapi_sheets_update_values(spreadsheet_id, range_name, value_input_option, values):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    curdir = os.getcwd()
    if '/hdd0/orca/' in curdir:
        auth_dir = '/hdd0/orca/orca_python/tokens/'
    else:
        auth_dir = 'C:/Users/APLUser/NEMO_Data/ESP_Processing/tokens'
    token_path = os.path.join(auth_dir, 'token.json')
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # pylint: disable=maybe-no-member
    try:
        service = build("sheets", "v4", credentials=creds)
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


# In[ ]:


def googleapi_batch_get_values(spreadsheet_id, range_names):
    """
    Creates the batch_update the user has access to.
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """

    curdir = os.getcwd()
    if '/hdd0/orca/' in curdir:
        auth_dir = '/hdd0/orca/orca_python/tokens/'
    else:
        auth_dir = 'C:/Users/APLUser/NEMO_Data/ESP_Processing/tokens'
    token_path = os.path.join(auth_dir, 'token.json')
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # pylint: disable=maybe-no-member
    try:
        service = build("sheets", "v4", credentials=creds)
        result = (
            service.spreadsheets()
            .values()
            .batchGet(spreadsheetId=spreadsheet_id, ranges=range_names)
            .execute()
        )
        ranges = result.get("valueRanges", [])
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


# # ESP Data Extraction Functions

# In[ ]:


def extract_esp_entry(esp_dataline):

    def convert_to_timestamp(entry):
        try:
            timeentry = pd.Timestamp(entry)
            if pd.isna(timeentry):
                return pd.NaT
            if timeentry.tzinfo is not None:
                timeentry = timeentry.tz_convert('UTC').tz_localize(None)
        except:
            timeentry = pd.NaT
        return timeentry

    def convert_to_float(entry):
        if entry in ('', None):
            return np.nan
        try:
            return float(entry)
        except:
            return np.nan

    esp_dataline = list(esp_dataline)
    if len(esp_dataline) < 23:
        esp_dataline.extend([''] * (23 - len(esp_dataline)))

    dep_lat = convert_to_float(esp_dataline[0])
    dep_lon = convert_to_float(esp_dataline[1])
    dep_start = convert_to_timestamp(esp_dataline[2])
    dep_end = convert_to_timestamp(esp_dataline[3])  
    dep_name = esp_dataline[4]
    dep_depth = convert_to_float(esp_dataline[5])
    samp_start = convert_to_timestamp(esp_dataline[6]).to_pydatetime()
    samp_end = convert_to_timestamp(esp_dataline[7]).to_pydatetime()
    target_vol = convert_to_float(esp_dataline[8])
    actual_vol = convert_to_float(esp_dataline[9])
    auto_time = convert_to_timestamp(esp_dataline[10]).to_pydatetime()
    auto_file = esp_dataline[11]
    auto_dur= convert_to_float(esp_dataline[12])
    first_time = convert_to_timestamp(esp_dataline[13]).to_pydatetime()
    first_file = esp_dataline[14]
    first_dur= convert_to_float(esp_dataline[15])
    sec_time = convert_to_timestamp(esp_dataline[16]).to_pydatetime()
    sec_file = esp_dataline[17]
    sec_dur= convert_to_float(esp_dataline[18])
    if esp_dataline[19] == '<LLOD':
        dem_acid = np.nan
    elif ('LLOD<' in esp_dataline[19]) and ('<LLOQ' in esp_dataline[19]):
        try:
            llod_str = esp_dataline[19].split('<LLOD')[1].split('<LLOQ')[0]
            llod_val = float(llod_str)
        except:
            dem_acid = np.nan
    else:
        dem_acid = convert_to_float(esp_dataline[19])
    llod = convert_to_float(esp_dataline[20])
    lloq = convert_to_float(esp_dataline[21])
    uloq = convert_to_float(esp_dataline[22])

    return (dep_lon, dep_lat, dep_start, dep_end, dep_name, dep_depth,
            samp_start, samp_end, target_vol, actual_vol,
            auto_time, auto_file, auto_dur,
            first_time, first_file, first_dur,
            sec_time, sec_file, sec_dur,
            dem_acid, llod, lloq, uloq)


# In[ ]:


def build_esp_metadict(metadata_rows):
    esp_metadict = {}
    for row in metadata_rows:
        esp_metadict[row[0].strip(':')] = row[1]

    return esp_metadict


# In[ ]:

def get_savedir():
    curdir = os.getcwd()
    if '/hdd0/orca/' in curdir:
        savedir = '/usr/local/share/data/erddap_data/esp_pnw_toxins/'
    else:
        savedir = 'C:/Users/APLUser/NEMO_Data/ESP_Processing/ESP_NetCDF/'
    return savedir


def make_esp_netcdf(esp_data, esp_metadict, esp_ncfile):

    savedir = get_savedir()
    esp_ncfile = os.path.join(savedir, esp_ncfile)
    tmpfile = 'tempfile.nc'

    print('   Open up a temporary netCDF with filename: ' + tmpfile)
    dataset = Dataset(tmpfile, 'w')
    successFlag = False

    def normalize_netcdf_string(value):
        if pd.isna(value):
            return ''
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        return str(value)

    string_columns = [
        'Deployment name',
        'Auto exposure image filename',
        'First fixed exposure image filename',
        'Second fixed exposure image filename',
    ]
    string_length = 1
    for column_name in string_columns:
        if column_name not in esp_data:
            continue
        for value in esp_data[column_name]:
            string_length = max(string_length, len(normalize_netcdf_string(value)))
    string_dtype = 'S' + str(string_length)

    def write_string_column(variable, column_name):
        values = np.asarray(
            [normalize_netcdf_string(value) for value in esp_data[column_name]],
            dtype=string_dtype
        )
        variable[0, :] = values

    try:
        dataset = em.populate_metadata(dataset, esp_metadict)

        # netCDF/ERDDAP Metadata
        dataset.history = ("Processing data into netCDF on " + 
                           datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S'))
        dataset.conventions = 'CF-1.6, ACDD-1.3, IOOS-1.2'
        dataset.platform_latitude = '47.9666N'
        dataset.platform_longitude = '-124.9458E'
        dataset.platform_water_depth = '100 m'
        fillVal = -555
        dataset._FillValue = fillVal
        dataset.cdm_data_type = 'timeSeries'
        dataset.cdm_timeseries_variables = 'location_id,latitude,longitude'
        dataset.subsetVariables = 'deployment_name'

        # The global attributes are needed to allow for ingesting by NDBC
        # into the GTS data harvester for models
        dataset.wmo_platform_code = ''
        dataset.gts_ingest = 'false'


         #################################################################
        # Create dimensions
        # format is "createDimension('dimension_name',n)"
        # Include descriptive attributes for each dimension

        nrows = len(esp_data)
        dataset.createDimension('location_id',1)
        dataset.createDimension('time',nrows)


        # First, create the dimensional variables    
        casttime = dataset.createVariable('time','f8',('location_id','time'))
        casttime.long_name = 'time'
        casttime.description = 'time of sampling'
        casttime.ancillary_variables = 'sample_starttime, sample_endtime'
        casttime.units = 'seconds since 1970-01-01 00:00:00'
        casttime.timezone = 'UTC'
        casttime.calendar = 'gregorian'

        # The variable "platform_name" is given the cf_role of "timeseries_id",
        # which is needed for CDM data types of "timeseries"
        depname = dataset.createVariable('deployment_name', string_dtype, ('location_id', 'time'))
        depname.long_name = 'deployment name'
        depname.description = 'Deployment designation'

        platform = dataset.createVariable('location_id', 'S7',
                                          ('location_id',))
        platform.long_name = 'location_id'
        platform.description = 'Buoy designation'
        platform.cf_role = 'timeseries_id'
        platform.units = '1'
        platform.ioos_category = 'Identifier'
        platform[0] = 'ESP_PNW'

        latitude = dataset.createVariable('latitude','f8',('location_id','time'))
        latitude.long_name = 'latitude'
        latitude.description = 'Latitude position in degrees North'
        latitude.units = 'degrees_north'

        longitude = dataset.createVariable('longitude','f8',('location_id','time'))
        longitude.long_name = 'longitude'
        longitude.description = 'Longitude position in degrees East'
        longitude.units = 'degrees_east'

        dep_startdate = dataset.createVariable('deployment_startdate','f8',('location_id','time'))
        dep_startdate.long_name = 'time'
        dep_startdate.description = 'start date of the deployment'
        dep_startdate.ancillary_variables = 'time, deployment_enddate'
        dep_startdate.units = 'seconds since 1970-01-01 00:00:00'
        dep_startdate.timezone = 'UTC'
        dep_startdate.calendar = 'gregorian'

        dep_enddate = dataset.createVariable('deployment_enddate','f8',('location_id','time'))
        dep_enddate.long_name = 'time'
        dep_enddate.description = 'end date of the deployment'
        dep_enddate.ancillary_variables = 'time, deployment_startdate'
        dep_enddate.units = 'seconds since 1970-01-01 00:00:00'
        dep_enddate.timezone = 'UTC'
        dep_enddate.calendar = 'gregorian'


        ##########################
        # Begin adding variables #
        ##########################

        # Sampling Times

        samp_starttime = dataset.createVariable('sample_starttime','f8',('location_id','time'))
        samp_starttime.long_name = 'time'
        samp_starttime.description = 'start time of sampling'
        samp_starttime.ancillary_variables = 'time, sample_endtime'
        samp_starttime.units = 'seconds since 1970-01-01 00:00:00'
        samp_starttime.timezone = 'UTC'
        samp_starttime.calendar = 'gregorian'
        samp_starttime.missing_value = fillVal
        samp_starttime._FillVal = fillVal

        samp_endtime = dataset.createVariable('sample_endtime','f8',('location_id','time'))
        samp_endtime.long_name = 'time'
        samp_endtime.description = 'end time of sampling'
        samp_endtime.ancillary_variables = 'time, sample_starttime'
        samp_endtime.units = 'seconds since 1970-01-01 00:00:00'
        samp_endtime.timezone = 'UTC'
        samp_endtime.calendar = 'gregorian'
        samp_endtime.missing_value = fillVal
        samp_endtime._FillVal = fillVal

        depth = dataset.createVariable('depth','f8',('location_id','time'))
        depth.long_name = 'depth'
        depth.description = 'target depth at which the sample was taken'
        depth.units = 'm'

        # Volume

        target_vol = dataset.createVariable('target_volume','f8',('location_id','time'))
        target_vol.long_name = 'target volume'
        target_vol.description = 'target sample volume'
        target_vol.units = 'mL'
        target_vol.missing_value = fillVal
        target_vol._FillVal = fillVal

        actual_vol = dataset.createVariable('actual_volume','f8',('location_id','time'))
        actual_vol.long_name = 'actual volume'
        actual_vol.description = 'actual sample volume'
        actual_vol.units = 'mL'
        actual_vol.missing_value = fillVal
        actual_vol._FillVal = fillVal

        # Auto Exposure Variables

        auto_time = dataset.createVariable('auto_exposure_time','f8',('location_id','time'))
        auto_time.long_name = 'Auto Exposure Timestamp'
        auto_time.description = 'Automatic Sampling Exposure Timestamp'
        auto_time.units = 'seconds since 1970-01-01 00:00:00'
        auto_time.timezone = 'UTC'
        auto_time.calendar = 'gregorian'
        auto_time.ancillary_variables = 'auto_image, auto_exposure_duration'

        auto_file = dataset.createVariable('auto_image', string_dtype, ('location_id','time'))
        auto_file.long_name = 'Auto Exposure Image'
        auto_file.description = 'Automatic Sampling Exposure Image Filename'
        auto_file.units = '1'
        auto_file.ancillary_variables = 'auto_exposure_time, auto_exposure_duration'

        auto_dur = dataset.createVariable('auto_exposure_duration','f8',('location_id','time'))
        auto_dur.long_name = 'Auto Exposure Duration'
        auto_dur.description = 'Automatic Sampling Exposure Time Duration'
        auto_dur.units = 'seconds'
        auto_dur.ancillary_variables = 'auto_exposure_time, auto_image'

        # First Exposure Variables

        first_time = dataset.createVariable('first_exposure_time','f8',('location_id','time'))
        first_time.long_name = 'First Fixed Exposure Timestamp'
        first_time.description = 'First Fixed Sampling Exposure Timestamp'
        first_time.units = 'seconds since 1970-01-01 00:00:00'
        first_time.timezone = 'UTC'
        first_time.calendar = 'gregorian'
        first_time.ancillary_variables = 'first_image, first_exposure_duration'

        first_file = dataset.createVariable('first_image', string_dtype, ('location_id','time'))
        first_file.long_name = 'First Fixed Exposure Image'
        first_file.description = 'First Fixed Sampling Exposure Image Filename'
        first_file.units = '1'
        first_file.ancillary_variables = 'first_exposure_time, first_exposure_duration'

        first_dur = dataset.createVariable('first_exposure_duration','f8',('location_id','time'))
        first_dur.long_name = 'First Fixed Exposure Duration'
        first_dur.description = 'First Fixed Sampling Exposure Time Duration'
        first_dur.units = 'seconds'
        first_dur.ancillary_variables  = 'first_exposure_time, first_image'

        # Second Exposure Variables

        sec_time = dataset.createVariable('second_exposure_time','f8',('location_id','time'))
        sec_time.long_name = 'Second Fixed Exposure Timestamp'
        sec_time.description = 'Second Fixed Sampling Exposure Timestamp'
        sec_time.units = 'seconds since 1970-01-01 00:00:00'
        sec_time.timezone = 'UTC'
        sec_time.calendar = 'gregorian'
        sec_time.ancillary_variables = 'second_image, second_exposure_duration'

        sec_file = dataset.createVariable('second_image', string_dtype, ('location_id','time'))
        sec_file.long_name = 'Second Fixed Exposure Image'
        sec_file.description = 'Second Fixed Sampling Exposure Image Filename'
        sec_file.units = '1'
        sec_file.ancillary_variables = 'second_exposure_time, second_exposure_duration'

        sec_dur = dataset.createVariable('second_exposure_duration','f8',('location_id','time'))
        sec_dur.long_name = 'Second Fixed Exposure Duration'
        sec_dur.description = 'Second Fixed Sampling Exposure Time Duration'
        sec_dur.units = 'seconds'
        sec_dur.ancillary_variables = 'second_exposure_time, second_image'

        # Sampling results

        dem_acid = dataset.createVariable('particulate_domoic_acid_concentraiton',
                                          'f8',('location_id','time'))
        dem_acid.long_name = 'particulate_domoic_acid_concentraiton'
        dem_acid.description = 'concentration of particular domoic acid'
        dem_acid.units = 'ng/L'
        dem_acid.missing_value = fillVal
        dem_acid._FillVal = fillVal

        llod = dataset.createVariable('lower_limit_of_detection',
                                      'f8',('location_id','time'))
        llod.long_name = 'lower_limit_of_detection'
        llod.description = 'Lowest value of domoic acid that can be detected'
        llod.units = 'ng/L'
        llod.missing_value = fillVal
        llod._FillVal = fillVal

        lloq = dataset.createVariable('lower_limit_of_quantification',
                                      'f8',('location_id','time'))
        lloq.long_name = 'lower_limit_of_quantification'
        lloq.description = 'Lowest value of domoic acid that can be quanitfied'
        lloq.units = 'ng/L'
        lloq.missing_value = fillVal
        lloq._FillVal = fillVal

        uloq = dataset.createVariable('upper_limit_of_quantification',
                                      'f8',('location_id','time'))
        uloq.long_name = 'upper_limit_of_quantification'
        uloq.description = 'Highest value of domoic acid that can be quanitfied'
        uloq.units = 'ng/L'
        uloq.missing_value = fillVal
        uloq._FillVal = fillVal


        #############################
        # Write data to each variable
        #############################

        reftime = datetime.datetime(1970,1,1)

        def to_epoch_seconds(value):
            timestamp = pd.Timestamp(value)
            if pd.isna(timestamp):
                return fillVal
            if timestamp.tzinfo is not None:
                timestamp = timestamp.tz_convert('UTC').tz_localize(None)
            return int((timestamp.to_pydatetime() - reftime).total_seconds())


        latitude[:] = esp_data['Deployment latitude']
        longitude[:] = esp_data['Deployment longitude']
        dep_startdate[:] = [to_epoch_seconds(ii)
                            for ii in esp_data['Date deployed']]
        dep_enddate[:] = [to_epoch_seconds(ii)
                          for ii in esp_data['Date retrieved']]
        write_string_column(depname, 'Deployment name')
        depth[:] = esp_data['Sample depth']


        sampstart = [to_epoch_seconds(ii)
                     for ii in esp_data['Sample start time']]
        casttime[:] = sampstart
        samp_starttime[:] = sampstart
        samp_endtime[:] = [to_epoch_seconds(ii)
                           for ii in esp_data['Sample end time']]

        target_vol[:] = esp_data['Target volume']
        actual_vol[:] = esp_data['Actual volume']

        auto_time[:] = [to_epoch_seconds(ii)
                        for ii in esp_data['Auto exposure image timestamp']]
        write_string_column(auto_file, 'Auto exposure image filename')
        auto_dur[:] = esp_data['Auto exposure time']

        first_time[:] = [to_epoch_seconds(ii)
                         for ii in esp_data['First fixed exposure image timestamp']]
        write_string_column(first_file, 'First fixed exposure image filename')
        first_dur[:] = esp_data['First fixed exposure time']

        sec_time[:] = [to_epoch_seconds(ii)
                       for ii in esp_data['Second fixed exposure image timestamp']]
        write_string_column(sec_file, 'Second fixed exposure image filename')
        sec_dur[:] = esp_data['Second fixed exposure time']

        dem_acid[:] = esp_data['Particulate domoic acid']
        llod[:] = esp_data['Lower limit of detection']
        lloq[:] = esp_data['Lower limit of quantification']
        uloq[:] = esp_data['Upper limit of quantification']

        # Update the successFlag to indicate
        # that all the data has been successfully
        # written to a netCDF
        successFlag = True

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print('Error occurred while making netCDF file.')
        print('Error occurred on line: ', exc_tb.tb_lineno)
        print(e)

    dataset.close()

    if successFlag:
        print('   Data has successfully been written to a netCDF.')
        print('   Move the temporary file to the updated file location.')
        print('   Updated file location: ' + esp_ncfile)
        shutil.move(tmpfile, esp_ncfile)

    return


# In[ ]:


def esp_datawrapper(data_year):

    # Define the Google sheet which ESP sheet ID
    esp_sheetid = '1ENQ87KecYPH8woFq4KGT061nCXCaNvqNc44I-PqKWkU'

    ##################
    # ESP Toxin Data #
    ##################

    # Get the columns of ESP Data
    print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') + 
          ' - Get column names from the Google Sheet')
    sheet_name = 'Data ' + str(int(data_year))
    esp_sheetcols = googleapi_batch_get_values(esp_sheetid, sheet_name+'!A1:W1')
    esp_columns = esp_sheetcols['valueRanges'][0]['values'][0]

    # Extract out each line of ESP data
    print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') + 
          ' - Get ESP data from the Google Sheet')
    esp_sheetdata = googleapi_batch_get_values(esp_sheetid, sheet_name+'!A2:W')
    esp_datalines = []
    for dataline in esp_sheetdata['valueRanges'][0]['values']:
        esp_datalines.append(extract_esp_entry(dataline))

    # Build a pandas dataframe of the ESP data
    print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') + 
          ' - Build a pandas dataframe of the data')
    esp_data = pd.DataFrame(columns=esp_columns,
                            data=esp_datalines)


    ######################
    # ESP Toxin Metadata #
    ######################
    print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') + 
              ' - Get dataset metadata from the Google Sheet')
    esp_metadata = googleapi_batch_get_values(esp_sheetid, 'Metadata!A1:B')
    esp_metadict = build_esp_metadict(esp_metadata['valueRanges'][0]['values'])


    ###################
    # Make the netCDF #
    ###################

    # Identify the deployment names
    deployment_names = np.unique(esp_data['Deployment name'])
    for deployment_name in deployment_names:

        esp_data_dep_subset = esp_data[esp_data['Deployment name'] == deployment_name].reset_index(drop=True)

        print(datetime.datetime.now().strftime('%Y-%b-%d %H:%M:%S') + 
              ' - Make the netCDF of the deployment: ' + deployment_name)
        deployment_filename = 'esp_pnw_toxins_' + deployment_name + '.nc'
        make_esp_netcdf(esp_data_dep_subset, esp_metadict, deployment_filename)

    return

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description='Download ESP toxin data for a deployment year and create per-deployment netCDF files.'
    )
    parser.add_argument(
        'data_year',
        type=int,
        help='Data year to read from the Google Sheet, for example 2025.'
    )
    return parser.parse_args(argv)


def main(argv=None):

    args = parse_args(argv)
    esp_datawrapper(args.data_year)
    return 0

if __name__ == "__main__":
    sys.exit(main())

