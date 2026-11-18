import os
import sys
import shutil
import argparse
from importlib import reload

def populate_metadata(dataset, esp_metadict):

    # Creator metadata
    dataset.creator_name = esp_metadict['creator_name']
    dataset.creator_email = esp_metadict['creator_email']
    dataset.creator_institution = esp_metadict['creator_institution']
    dataset.creator_url = esp_metadict['creator_url']
    dataset.creator_sector = esp_metadict['creator_sector']
    dataset.creator_type = esp_metadict['creator_type']
    dataset.creator_country = esp_metadict['creator_country']

    # Publisher metadata
    dataset.publisher_name = esp_metadict['publisher_name']
    dataset.publisher_email = esp_metadict['publisher_email']
    dataset.publisher_institution = esp_metadict['publisher_institution']
    dataset.publisher_url = esp_metadict['publisher_url']
    dataset.publisher_type = esp_metadict['publisher_type']
    dataset.publisher_country = esp_metadict['publisher_country']

    # Contributors metadata
    dataset.contributor_name = esp_metadict['contributor_name']
    dataset.contributor_email = esp_metadict['contributor_email']
    dataset.contributor_institution = esp_metadict['contributor_institution']
    dataset.contributor_role = esp_metadict['contributor_role']
    dataset.contributor_url = esp_metadict['contributor_url']

    # Dataset Metadata
    dataset.title = esp_metadict['title']
    dataset.program = esp_metadict['program']
    dataset.program_url = esp_metadict['program_url']
    dataset.summary = esp_metadict['summary']
    dataset.citation = esp_metadict['citation']
    dataset.linked_datasets = esp_metadict['linked_datasets']
    dataset.references = esp_metadict['references']

    # ESP Sampler Metadata
    dataset.esp_serial_number = esp_metadict['esp_serial_number']
    dataset.esp_instrument_type = esp_metadict['esp_instrument_type']
    dataset.collection_filter_type = esp_metadict['collection_filter_type']
    dataset.collection_filter_porosity = esp_metadict['collection_filter_porosity']
    dataset.nominal_location = esp_metadict['nominal_location']
    dataset.method = esp_metadict['method']

    return dataset