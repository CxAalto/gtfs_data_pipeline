import os
from gtfspy import util
from research.route_diversity.diversity_settings import string_to_add


COUNTRY_FEED_LIST = ['denmark', 'sweden', 'finland-matka', 'belgium', 'switzerland', 'israel', 'netherlands', 'norway']

__THIS_DIR = os.path.dirname(os.path.realpath(__file__))

RAW_DATA_DIR = os.path.normpath(os.path.join(__THIS_DIR, "../../scratch/rawgtfs/"))
assert os.path.exists(RAW_DATA_DIR)
ALL_RAW_GTFS_DIRS = []
TO_PUBLISH_ROOT_OUTPUT_DIR = os.path.join("/home/clepe/route_diversity/data/cities")
INTRO_ANALYSIS_DIR = os.path.join("/home/clepe/scratch/diversity_data/intro_analysis")
INTRO_PICKLE = os.path.join(INTRO_ANALYSIS_DIR, "intro.pickle")
MEASURES = ['number_of_route_variants', 'cross_route_ratio', 'route_length', 'route_section_length',
                         'route_kilometrage', 'prop_length_peak', 'prop_section_length_peak', 'prop_kilometrage_peak',
                         'avg_segment_frequency_peak', 'route_overlap_peak', 'prop_length_day',
                         'prop_section_length_day', 'prop_kilometrage_day', 'avg_segment_frequency_day',
                         'route_overlap_day', 'mean_jaccard', 'mean_service_hours', 'weighted_mean_service_hours',
                         'long_service_hour_kms', 'long_service_hour_prop']
# TO_PUBLISH_ROOT_OUTPUT_DIR = os.path.join(__THIS_DIR, "../../scratch/to_publish/")

# TO_PUBLISH_ROOT_OUTPUT_DIR = os.path.join(__THIS_DIR, "copies_from_hammer/")
COUNTRY_FEEDS_DIR = os.path.join(__THIS_DIR, "../../scratch/country_feeds_for_publish")
PATH_TO_PUBLISH_CSV = os.path.join("/home/clepe/transit/research/route_diversity/", string_to_add + "diversity_to_publish.csv")
#COORDINATE_CORRECTIONS_CSV = os.path.join("/home/clepe/transit/research/route_diversity/diversity_to_publish.csv")
SQLITE_ENDING = ".sqlite"

THUMBNAIL_DIR = os.path.join(__THIS_DIR, TO_PUBLISH_ROOT_OUTPUT_DIR, "thumbnails/")
util.makedirs(THUMBNAIL_DIR)

GTFS_ZIPFILE_BASENAME = "gtfs.zip"
