import os

# This location ("../scratch/") is specific to Aalto University premises
# Change to fit your needs.
RAW_DATA_DIR_PARENT_DIR = '../scratch'

print("Data will be donwloaded to " + RAW_DATA_DIR_PARENT_DIR)
assert os.path.exists(RAW_DATA_DIR_PARENT_DIR)
