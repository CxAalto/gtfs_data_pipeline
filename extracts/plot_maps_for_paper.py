import os

import numpy
import matplotlib as mpl
print("current backend is %s" % mpl.get_backend())
mpl.use('TkAgg')

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

from create_multiple_extracts import ALL_CITIES
from extract_pipeline import ExtractPipeline
from gtfspy.gtfs import GTFS
from gtfspy.mapviz import plot_route_network_from_gtfs
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple
from settings import TO_PUBLISH_ROOT_OUTPUT_DIR

FIG_PATH_DIR = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "full_route_map_images/")


def plot_city_figs(cities=None, axes=None, save_figure=True):
    if cities is None:
        cities = sorted(ALL_CITIES)
    for i, city in enumerate(cities):
        print("Plotting " + city)
        if axes is not None:
            ax = axes[i]
        else:
            fig = plt.figure(figsize=(6.,4.))
            ax = fig.add_subplot(111)
            fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
        to_publish_csv = get_to_publish_csv()
        city_data = to_publish_csv[to_publish_csv["id"] == city].iloc[0]
        feeds = get_feeds_from_to_publish_tuple(city_data)
        pipeline = ExtractPipeline(city_data, feeds)
        try:
            day_G = GTFS(pipeline.day_db_path)
            ax = plot_route_network_from_gtfs(day_G, map_style="dark_all", ax=ax)
        except FileNotFoundError as e:
            print("File " + pipeline.day_db_path + " was not found")
        if save_figure:
            fig_path = os.path.join(FIG_PATH_DIR, city + ".pdf")
            ax.figure.savefig(fig_path)
            print("Figure saved to: \n" + fig_path)
    # plt.show()


def plot_overall_map(ax=None, save_figure=True):
    if ax is None:
        fig = plt.figure(figsize=(10.0, 4.0))
        ax = fig.add_subplot(111)

    # Get coordinates of all cities, and plot them on a map.
    # Red dots on a whitish background should do?
    to_publish_csv = get_to_publish_csv()
    cities_to_plot = to_publish_csv[to_publish_csv['id'].isin(ALL_CITIES)]
    lons = cities_to_plot['lon'].values
    lats = cities_to_plot['lat'].values

    map = Basemap(projection="robin", lon_0=0, ax=ax)
    # plot coastlines, draw label meridians and parallels.
    map.drawcoastlines(linewidth=0.5)
    map.drawparallels(numpy.arange(-90, 90, 30), labels=[1, 0, 0, 0])
    map.drawmeridians(numpy.arange(map.lonmin, map.lonmax + 30, 60), labels=[0, 0, 0, 1])
    # fill continents 'coral' (with zorder=0), color wet areas 'aqua'
    map.drawmapboundary(fill_color='#dbe8ff')
    map.fillcontinents(color='white', lake_color='#dbe8ff')
    print(lons)
    print(lats)
    lons, lats = map(lons,lats)
    map.scatter(list(lons), list(lats), color="red", latlon=False, s=40, zorder=10)

    if save_figure:
        fname = os.path.join(FIG_PATH_DIR, "overall_map.pdf")
        print("Saving the overall map to: " + fname)
        plt.savefig(fname)
        plt.show()

if __name__ == "__main__":
    try:
        os.mkdir(FIG_PATH_DIR)
    except FileExistsError:
        pass
    print("Saving map figures to " + FIG_PATH_DIR)

    # plot_city_figs()

    fig = plt.figure(figsize=(8, 8))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)
    ax = fig.add_subplot(2, 1, 1)
    plot_overall_map(ax, save_figure=False)
    axes = [fig.add_subplot(2, 2, 3), fig.add_subplot(2, 2, 4)]
    plot_city_figs(["rome", "winnipeg"], axes=axes, save_figure=False)
    filepath = os.path.join(FIG_PATH_DIR, "paper_fig.pdf")
    # fig.tight_layout()
    print("Saving paper map figure to " + filepath)
    # plt.show()
    fig.savefig(filepath)
    fig.savefig(filepath.replace("pdf", "svg"))
