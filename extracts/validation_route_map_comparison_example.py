import os
import pandas


from extract_pipeline import ExtractPipeline
from create_multiple_extracts import ALL_CITIES
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple

from matplotlib import pyplot as plt
from gtfspy.mapviz import plot_route_network_from_gtfs, plot_as_routes
from gtfspy.gtfs import GTFS
from gtfspy.stats import get_spatial_bounds

from settings import TO_PUBLISH_ROOT_OUTPUT_DIR
FIG_PATH_DIR = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "full_route_map_images/")




def get_node_I_to_coords_dicts(pipeline):
    nodes = pandas.read_csv(pipeline.network_node_info_fname,sep=";")
    assert len(nodes.columns) > 2

    nodeI_to_lat = dict()
    nodeI_to_lon = dict()
    for node_row in nodes.itertuples():
        nodeI_to_lat[node_row.stop_I] = node_row.lat
        nodeI_to_lon[node_row.stop_I] = node_row.lon
    return nodeI_to_lat, nodeI_to_lon


def point_within_bounds(lat, lon, spatial_bounds):
    if lat < spatial_bounds['lat_max'] and lat > spatial_bounds['lat_min'] and lon < spatial_bounds['lon_max'] and lon > spatial_bounds['lon_min']:
        return True
    return False

def plot_static_nets():
    for city in ALL_CITIES:
        to_publish_csv = get_to_publish_csv()
        city_data = to_publish_csv[to_publish_csv["id"] == city].iloc[0]
        feeds = get_feeds_from_to_publish_tuple(city_data)
        pipeline = ExtractPipeline(city_data, feeds)
        nodeI_to_lat, nodeI_to_lon = get_node_I_to_coords_dicts(pipeline)

        if city == "helsinki":
            spatial_bounds = {
                "lon_min": 24.890866,  # min(nodes.lon),
                "lon_max": 24.988235,  # max(nodes.lon),
                "lat_min": 60.146590,  # min(nodes.lat),
                "lat_max": 60.187246  # max(nodes.lat)
            }
        else:
            spatial_bounds = {
                "lon_min": min(nodeI_to_lon.values()),
                "lon_max": max(nodeI_to_lon.values()),
                "lat_min": min(nodeI_to_lat.values()),
                "lat_max": max(nodeI_to_lat.values())
            }

        static_net = pandas.read_csv(pipeline.network_combined_fname, sep=";")
        assert len(static_net.columns) > 2
        plot_edges = []
        for edge in static_net.to_dict("records"):
            # name, type, agency, lats, lons = []
            plot_edge = {
                "type": edge['route_type'],
                "lats": (nodeI_to_lat[edge['from_stop_I']], nodeI_to_lat[edge['to_stop_I']]),
                "lons": (nodeI_to_lon[edge['from_stop_I']], nodeI_to_lon[edge['to_stop_I']])
            }
            pe = plot_edge
            if point_within_bounds(pe["lats"][0], pe["lons"][0], spatial_bounds) or point_within_bounds(pe["lats"][1], pe["lons"][1], spatial_bounds):
                plot_edges.append(plot_edge)
        ax = plot_as_routes(plot_edges, spatial_bounds, map_style="dark_all")
        ax.figure.savefig("/tmp/new_filter/static_network_" + city + ".pdf")
        print("plotted static network for " + city)
        plt.close(ax.figure)



def plot_event_distributions():
    for example_city in ALL_CITIES: # ["kuopio", "prague"]:
        for time_interval in ["week", "day"]:

            to_publish_csv = get_to_publish_csv()
            city_data = to_publish_csv[to_publish_csv["id"] == example_city].iloc[0]
            feeds = get_feeds_from_to_publish_tuple(city_data)
            pipeline = ExtractPipeline(city_data, feeds)

            weekly_extract_start_date = pipeline.get_weekly_extract_start_date()
            assert weekly_extract_start_date.weekday() == 0
            day_start_ut = GTFS(pipeline.day_db_path).get_day_start_ut(weekly_extract_start_date)

            if time_interval == "week":
                events = pandas.read_csv(pipeline.temporal_network_week_fname, sep=";")
            else:
                events = pandas.read_csv(pipeline.temporal_network_fname, sep=";")
            assert len(events.columns) > 2
            fig, ax = plt.subplots()
            ax.hist(events['dep_time_ut'], bins=200)
            print(weekly_extract_start_date.weekday(), min(events['dep_time_ut']))
            fig.suptitle(example_city)
            multiplier = 1
            if time_interval == "week":
                multiplier = 7
            ax.axvline(day_start_ut, label="monday 0AM", color="C1")
            ax.axvline(day_start_ut + 3 * 3600, label="monday 3AM", color="C2")
            ax.axvline(day_start_ut + multiplier * 24 * 3600, label="tuesday 0AM", color="C3")
            ax.axvline(day_start_ut + multiplier * 24 * 3600 + 3 * 3600, label="tuesday 3AM", color="C4")
            ax.legend()
            fig.savefig("/tmp/new_filter/event_departures_" + example_city + "_" + time_interval + ".pdf")
            plt.close(fig)

plot_static_nets()
# plot_event_distributions()


