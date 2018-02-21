import os

from extract_pipeline import ExtractPipeline
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple


from matplotlib import pyplot as plt
from gtfspy.gtfs import GTFS
from gtfspy.mapviz import plot_route_network_from_gtfs

from settings import TO_PUBLISH_ROOT_OUTPUT_DIR
FIG_PATH_DIR = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "full_route_map_images/")

example_city = "rome"

fig = plt.figure(figsize=(6, 4.))
ax1 = fig.add_subplot(111)

to_publish_csv = get_to_publish_csv()
city_data = to_publish_csv[to_publish_csv["id"] == example_city].iloc[0]
feeds = get_feeds_from_to_publish_tuple(city_data)
pipeline = ExtractPipeline(city_data, feeds)

# plot merged data without any filtering
fig, ax = pipeline.plot_weekly_extract_start_and_download_dates(given_axes=ax1)
fig.tight_layout()
fig.savefig(FIG_PATH_DIR + "temporal_filtering_example_figure_base.pdf")

plt.show()




