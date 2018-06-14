### Introduction
This repository contains code for automated downloading and storage of GTFS data, and the subsequent processing of the GTFS data into public transport network extracts covering individual cities. 

This pipeline was used to reproduce data depositoted in Zenodo https://doi.org/10.5281/zenodo.1186215 (and described in paper http://doi.org/10.1038/sdata.2018.89).

The two main steps of this process are

1. Downloading of source data (using `gtfs_scrape.sh`)
    (A separate credentials-file like `credentials_template.yaml` is required)
2. Processing the downloaded data further with (`extracts/create_multiple_extracts.py`)
    (Remember also to set associated settings correctly (`extracts/settings.py`))

### Contents of gtfs_data_pipeline/

- `download/`:
    Downloading of GTFS-feeds.
- `extracts/`:
    Code for importing the raw downloaded data, and transforming that
    data into publication extracts.
    - `coordinate_corrections.csv`:
        List of coordinates to change in the publication extracts.
    - `to_publish.csv`:
        Master specification of the extracts we will publish.
- `gtfs-sources.yaml`:
    Data on the gtfs-sources we have been downloading.
- `gtfs_scrape.sh`:
    Helper script to do the weekly download.
- `credentials.yaml`:
    A (symbolic) link to the credentials (not present in the repository, create your own!)
- `credentials_template.yaml`:
    An example credentials file. 

### Authors:
Rainer Kujala, Christoffer Weckström, Richard Darst
