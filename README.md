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
- 'credentials.yaml':
    A (symbolic) link to the credentials (not present in the repository, create your own!)
- 'credentials_template.yaml':
    An example credentials file.

### Authors:
Rainer Kujala, Christoffer Weckström, Richard Darst
