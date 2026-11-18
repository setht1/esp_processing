# esp_processing
Process ESP Sampler data into ERDDAP-compatible netCDF files

# Background
Information on the ESP Sampler

# Goal
The esp_dataprocessing python script will be capable of processing the output data for each deployment of the ESP sampler. It will read in the data from an Excel spreadsheet, provided with one spreadsheet per deployment, and write the data into an ERDDAP-compliant netCDF file for hosting on the NWEM web server. Additionally, it will update the source of the image file for each sample, based upon whether the NWEM webserver or NCEI will be the final sourcing destination.

The script will be able to be run for a single deployment, given as input arguments, or run on all deployments (the default option).

# Structure:
esp_dataprocessing.py - Main data processing script
esp_metadata.py       - Sub-script which contains functions to help populate the metadata of the netCDF generation
--deployment_data     - Folder which contains all of the Excel spreadsheets to be read and processed
--processed_data      - Folder which contains all of the processed netCDFs
--reference_info      - Folder which contains relevant reference information, including processing directory information, and
                        deployment information
