import os

from extract_pipeline import ExtractPipeline
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple


from matplotlib import pyplot as plt
from gtfspy.gtfs import GTFS
from gtfspy.mapviz import plot_route_network_from_gtfs

from settings import TO_PUBLISH_ROOT_OUTPUT_DIR
FIG_PATH_DIR = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "full_route_map_images/")

example_city = "dublin"

fig = plt.figure(figsize=(9., 3.))
ax1 = fig.add_subplot(131)
ax2 = fig.add_subplot(132)
ax3 = fig.add_subplot(133)
fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)

to_publish_csv = get_to_publish_csv()
city_data = to_publish_csv[to_publish_csv["id"] == example_city].iloc[0]
feeds = get_feeds_from_to_publish_tuple(city_data)
pipeline = ExtractPipeline(city_data, feeds)

# custom spatial bounds
spatial_bounds = {'lat_max': 53.5187041352142,
                  'lat_min': 53.187898120044203,
                  'lon_min': -6.5567194744694799,
                  'lon_max': -6.0545860833062104}
offset_lat = (spatial_bounds['lat_max'] - spatial_bounds['lat_min']) * 0.15
offset_lon = (spatial_bounds['lon_max'] - spatial_bounds['lon_min']) * 0.2
spatial_bounds['lat_max'] += offset_lat
spatial_bounds['lat_min'] -= offset_lat
spatial_bounds['lon_max'] += offset_lon
spatial_bounds['lon_min'] -= offset_lon


# plot merged data without any filtering
raw_G = GTFS(pipeline.raw_db_path)
plot_route_network_from_gtfs(raw_G, map_style="dark_all", ax=ax1)

# plot merged data without any filtering
raw_G = GTFS(pipeline.raw_db_path)
plot_route_network_from_gtfs(raw_G, map_style="dark_all", ax=ax2, spatial_bounds=spatial_bounds)

# plot merged data after spatial filtering
day_G = GTFS(pipeline.day_db_path)
plot_route_network_from_gtfs(day_G, map_style="dark_all", ax=ax3, spatial_bounds=spatial_bounds)

fig.savefig(FIG_PATH_DIR + "spatial_filtering_example_figure_base.pdf")
plt.show()




