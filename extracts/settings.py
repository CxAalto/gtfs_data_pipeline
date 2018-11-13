import os
from gtfspy import util


COUNTRY_FEED_LIST = ['denmark', 'sweden', 'finland-matka', 'belgium', 'switzerland', 'israel', 'netherlands', 'norway']

__THIS_DIR = os.path.dirname(os.path.realpath(__file__))

RAW_DATA_DIR = os.path.join(__THIS_DIR, "../../scratch/rawgtfs/")
assert os.path.exists(RAW_DATA_DIR)
ALL_RAW_GTFS_DIRS = []
TO_PUBLISH_ROOT_OUTPUT_DIR = os.path.join("/home/clepe/route_diversity/data/cities")
# TO_PUBLISH_ROOT_OUTPUT_DIR = os.path.join(__THIS_DIR, "../../scratch/to_publish/")

# TO_PUBLISH_ROOT_OUTPUT_DIR = os.path.join(__THIS_DIR, "copies_from_hammer/")
COUNTRY_FEEDS_DIR = os.path.join(__THIS_DIR, "../../scratch/country_feeds_for_publish")
PATH_TO_PUBLISH_CSV = os.path.join("/home/clepe/transit/research/route_diversity/diversity_to_publish.csv")
#COORDINATE_CORRECTIONS_CSV = os.path.join("/home/clepe/transit/research/route_diversity/diversity_to_publish.csv")
SQLITE_ENDING = ".sqlite"

THUMBNAIL_DIR = os.path.join(__THIS_DIR, TO_PUBLISH_ROOT_OUTPUT_DIR, "thumbnails/")
util.makedirs(THUMBNAIL_DIR)

GTFS_ZIPFILE_BASENAME = "gtfs.zip"
