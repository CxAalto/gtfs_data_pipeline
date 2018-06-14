### Contents

#### Main

- `create_multiple_extracts.py`:
    The main script used for importing and deploying a city to transportnetworks.cs.aalto.fi
- `settings.py`:
    Various settings related to data storage etc., i.e. information on various input and output file paths.

#### Core parts
- `extract_pipeline.py`:
    Code for steering the import pipeline for one city. 
- `feed_manager.py`:
    Code for checking the availability of the feeds.
- `read_to_publish_csv.py`:
    Reads in the to_publish_csv
- `licenses/`:
    Code and material for documenting the licensing terms of each fed.

