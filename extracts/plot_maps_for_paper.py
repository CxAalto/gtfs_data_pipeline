import os

import numpy
import matplotlib
matplotlib.use("macosx")

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

from create_multiple_extracts import ALL_CITIES
from extract_pipeline import ExtractPipeline
from gtfspy.gtfs import GTFS
from gtfspy.mapviz import plot_route_network_from_gtfs
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple
from settings import TO_PUBLISH_ROOT_OUTPUT_DIR

from matplotlib import rcParams
rcParams['figure.figsize'] = (12.0, 12.0)

FIG_PATH_DIR = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "full_route_map_images/")


def plot_city_figs():
    rcParams['figure.figsize'] = (12.0, 12.0)
    for city in sorted(ALL_CITIES):
        print("Plotting " + city)
        to_publish_csv = get_to_publish_csv()
        city_data = to_publish_csv[to_publish_csv["id"] == city].iloc[0]
        feeds = get_feeds_from_to_publish_tuple(city_data)
        pipeline = ExtractPipeline(city_data, feeds)
        try:
            day_G = GTFS(pipeline.day_db_path)
            ax = plot_route_network_from_gtfs(day_G, map_style="dark_all")
            fig_path = os.path.join(FIG_PATH_DIR, city + ".pdf")
            ax.figure.savefig(fig_path)
            print("Figure saved to: \n" + fig_path)
        except FileNotFoundError as e:
            print("File " + pipeline.day_db_path + " was not found")




def plot_overall_map():
    # Get coordinates of all cities, and plot them on a map.
    # Red dots on a whitish background should do?
    to_publish_csv = get_to_publish_csv()
    publishable = to_publish_csv[to_publish_csv["publishable"] == "1"]
    print(publishable)
    lons = publishable['lon'].values
    lats = publishable['lat'].values

    print(lons, lats)
    # miller projection
    map = Basemap(projection="robin", lon_0=0)
    # plot coastlines, draw label meridians and parallels.
    map.drawcoastlines()
    map.drawparallels(numpy.arange(-90, 90, 30), labels=[1, 0, 0, 0])
    map.drawmeridians(numpy.arange(map.lonmin, map.lonmax + 30, 60), labels=[0, 0, 0, 1])
    # fill continents 'coral' (with zorder=0), color wet areas 'aqua'
    map.drawmapboundary(fill_color='#dbe8ff')
    map.fillcontinents(color='white', lake_color='#dbe8ff')
    map.scatter(lons, lats, color="red", latlon=True, s=80, zorder=10)

    # shade the night areas, with alpha transparency so the
    # map shows through. Use current time in UTC.
    fname = os.path.join(FIG_PATH_DIR, "overall_map.pdf")
    print("Saving the overall map to: " + fname)
    plt.savefig(fname)

if __name__ == "__main__":
    rcParams['figure.figsize'] = (10.0, 6.0)
    try:
        os.mkdir(FIG_PATH_DIR)
    except FileExistsError:
        pass
    print("Saving map figures to " + FIG_PATH_DIR)

    plot_overall_map()