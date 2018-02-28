import datetime
import os
import subprocess
import sys
from os import listdir
from zipfile import ZipFile
import zipfile

import pandas
import yaml

from feed_manager import FeedManager
from gtfspy import exports, filter, import_validator, timetable_validator, util
from gtfspy.gtfs import GTFS
from gtfspy.aggregate_stops import aggregate_stops_spatially
from gtfspy.networks import combined_stop_to_stop_transit_network
from licenses.adapt_licenses import create_license_files
from read_to_publish_csv import to_publish_generator
from settings import COUNTRY_FEED_LIST, TO_PUBLISH_ROOT_OUTPUT_DIR, SQLITE_ENDING, COUNTRY_FEEDS_DIR, \
    THUMBNAIL_DIR, GTFS_ZIPFILE_BASENAME
from city_notes import CITY_ID_TO_NOTES_STR

"""
This script finds, imports, filters and validates one or several raw gtfs files.

Preparations:
- Identify needed rawfolders from to_publish.csv ->
  browse trough all; create list of all feeds: city, feed, date1, date2, date3...
- Check that all subfeeds are available for the wanted extract period (download date).
  Note that some subfeeds have been renamed.

Input: rawfolder, download date, city, to_publish.csv

See ExtractPipeline.run_full_without_deploy for details on what is done.
"""

import matplotlib
#matplotlib.use("agg")
matplotlib.use("TkAgg") # use this if interactive visualizations are wanted


AVAILABLE_COMMANDS = ['full',
                      "thumbnail",
                      "licenses",
                      "create_networks",
                      "clear",
                      "deploy_to_server",
                      "copy_from_hammer",
                      "import_raw",
                      "clear_main",
                      "stats",
                      "extract_start_date",
                      "notes",
                      "extracts"]

SUCCESS = True

def main():
    try:
        command = sys.argv[1]
    except IndexError:
        print("Options: ")
        print(", ".join(AVAILABLE_COMMANDS))

    try:
        param1 = sys.argv[2]
    except IndexError:
        param1 = None

    try:
        param2 = sys.argv[3]
        if param2 == "None":
            param2 = None
    except IndexError:
        param2 = None

    if command == 'status':
        if param1:
            FeedManager().write_complete_feeds_status(complete_feeds_path=param1)
        else:
            FeedManager().write_complete_feeds_status()
    elif command in AVAILABLE_COMMANDS:
        city = param1
        download_date_override = param2
        for to_publish_tuple, feeds in to_publish_generator():
            if city == to_publish_tuple.id or city == 'all':
                pipeline = ExtractPipeline(to_publish_tuple, feeds, download_date=download_date_override)
                try:
                    if command == "import_raw":
                        pipeline.import_original_feeds_into_raw_db()
                    elif command == "full":
                        pipeline.run_full_without_deploy()
                    elif command == "licenses":
                        pipeline._create_license_files()
                    elif command == "thumbnail":
                        pipeline.create_thumbnail_for_web()
                    elif command == "deploy_to_server":
                        pipeline.assert_contents_exist()
                        pipeline.create_zip()
                        pipeline.deploy_to_transportnetorks_cs_aalto()
                    elif command == "clear":
                        pipeline.clear()
                    elif command == "stats":
                        pipeline._write_stats()
                    elif command == "clean":
                        pipeline.remove_temporary_files()
                    elif command == "clear_main":
                        pipeline.clear()
                        pipeline._create_raw_db()
                        pipeline._main_db_extract()
                    elif command == "create_networks":
                        pipeline._create_network_extracts()
                    elif command == "extracts":
                        pipeline._create_data_extracts()
                    elif command == "extract_start_date":
                        pipeline.plot_weekly_extract_start_and_download_dates()
                    elif command == "notes":
                        pipeline._write_city_notes()
                except Exception as e:
                    print("Something went wrong when trying to run the ExtractPipeline with ",
                          to_publish_tuple.id, to_publish_tuple.download_date, command, " :")
                    print(e)
                    import traceback
                    # pipeline._write_main_db_warnings(extra_str=str(e) + "\n ")
                    print(command + " for ", to_publish_tuple.id, " failed")
                    print('=' * 40)
                    traceback.print_exc()
                    print('=' * 40)
                    print("Log file written in: " + pipeline.log_fname)
    else:
        print("Example usage: extract_pipeline.py full detroit")
        print("Available commands:" + ",".join(AVAILABLE_COMMANDS))


def flushed(method):
    def _flushed(*args, **kw):
        print("Starting " + method.__name__)
        sys.stdout.flush()
        result = method(*args, **kw)
        sys.stdout.flush()
        return result
    return _flushed


class ExtractPipeline(object):

    TEMP_FILE_PREFIX = "temporary_file_"

    def __init__(self, city_publish_tuple, feeds=None,
                 download_date=None):
        # print(city_publish_tuple, feeds, download_date)

        # Feed parameters
        self.feeds = feeds
        self.city_id = city_publish_tuple.id

        self.lat = float(city_publish_tuple.lat)
        self.lon = float(city_publish_tuple.lon)
        self.publishable = city_publish_tuple.publishable
        self.extract_start_date = city_publish_tuple.extract_start_date

        self.buffer_distance = float(city_publish_tuple.buffer)
        self.name = city_publish_tuple.name

        if not download_date:
            if city_publish_tuple.download_date:
                self.download_date = city_publish_tuple.download_date
            else:
                raise Exception('No download date specified!')
        else:
            self.download_date = download_date

        # Create output directory:
        assert isinstance(self.city_id, str)
        assert isinstance(self.download_date, str)
        self.output_directory = util.makedirs(os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, self.city_id, self.download_date))

        # create
        if any(x in self.feeds for x in COUNTRY_FEED_LIST):
            country_feed = [feed for feed in self.feeds if feed in COUNTRY_FEED_LIST]
            country_feed = country_feed[0]
            output_sub_dir_country = util.makedirs(os.path.join(COUNTRY_FEEDS_DIR, country_feed, self.download_date))
            self.raw_db_path = os.path.join(output_sub_dir_country, ExtractPipeline.TEMP_FILE_PREFIX + SQLITE_ENDING)
        else:
            self.raw_db_path = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + SQLITE_ENDING)


        self.main_db_path = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + "_main" + SQLITE_ENDING)
        self.week_db_path = os.path.join(self.output_directory, "week" + SQLITE_ENDING)
        self.day_db_path = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + "_day" + SQLITE_ENDING)

        self.week_gtfs_path = os.path.join(self.output_directory, "week." + GTFS_ZIPFILE_BASENAME)

        self.temporal_network_fname = os.path.join(self.output_directory, "network_temporal_day.csv")
        self.temporal_network_week_fname = os.path.join(self.output_directory, "network_temporal_week.csv")
        self.network_node_info_fname = os.path.join(self.output_directory, "network_nodes.csv")
        self.network_combined_fname = os.path.join(self.output_directory, "network_combined.csv")

        self.stops_geojson_fname = os.path.join(self.output_directory, "stops.geojson")
        self.sections_geojson_fname = os.path.join(self.output_directory, "sections.geojson")
        self.routes_geojson_fname = os.path.join(self.output_directory, "routes.geojson")

        self.stats_fname = os.path.join(self.output_directory, "stats.csv")

        self.notes_fname = os.path.join(self.output_directory, "notes.txt")

        self.log_fname = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, self.city_id + "_" + self.download_date + ".txt")

        self.coordinate_corrections = pandas.read_csv("coordinate_corrections.csv", sep=",")

        # GTFS Warning containers:
        self.tv_warnings = None  # timetable validation warnings
        self.iv_warnings = None  # import validation warnings

        self.raw_import_warnings_summary_fname = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + "raw_db_import_warnings_summary.log")
        self.raw_import_warnings_details_fname = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + "raw_db_import_warnings_details.log")

        self.main_db_timetable_warnings_summary_fname= os.path.join(self.output_directory,  ExtractPipeline.TEMP_FILE_PREFIX + "main_db_timetable_warnings_summary.log")
        self.main_db_timetable_warnings_details_fname = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + "main_db_timetable_warnings_details.log")

        self.week_db_timetable_warnings_summary_fname = os.path.join(self.output_directory, "week_db_timetable_warnings_summary.log")
        self.week_db_timetable_warnings_details_fname = os.path.join(self.output_directory, ExtractPipeline.TEMP_FILE_PREFIX + "week_db_timetable_warnings_details.log")

        self.weekly_extract_dates_plot_fname = os.path.join(self.output_directory,
                                                            ExtractPipeline.TEMP_FILE_PREFIX + "extract_start_date_plot.pdf")
        self.thumbnail_path = os.path.join(self.output_directory, "thumbnail.jpg")
        self.zip_file_name = os.path.join(self.output_directory, self.city_id + ".zip")

    @flushed
    def clear(self):
        for filename in os.listdir(self.output_directory):
            full_path_filename = os.path.join(self.output_directory, filename)
            os.remove(full_path_filename)
            print("removing" + full_path_filename)

    @flushed
    def remove_temporary_files(self):
        """ Remove each file that starts with toremove """
        for filename in os.listdir(self.output_directory):
            if ExtractPipeline.TEMP_FILE_PREFIX in filename:
                full_path_filename = os.path.join(self.output_directory, filename)
                os.remove(full_path_filename)
                print("removing" + full_path_filename)

    @flushed
    def _create_license_files(self):
        create_license_files(self.city_id, self.output_directory)

    @flushed
    def run_full_without_deploy(self):
        """
        This function orchestrates the import process for each city.
        """
        self._create_raw_db()
        self._main_db_extract()
        self._write_main_db_validation_warnings()
        self._compute_stop_distances_osm_for_main_db()
        self._create_data_extracts()
        self._write_city_notes()
        self.create_thumbnail_for_web()

    @flushed
    def _create_raw_db(self):
        self.import_original_feeds_into_raw_db()
        self._correct_coordinates_for_raw_db()
        self._correct_arrival_times_for_raw_db()
        self._validate_raw_db_and_write_warnings()
        self._aggregate_stops_with_same_location()

    @flushed
    def _create_data_extracts(self):
        self._create_week_db_extract()
        self._validate_week_db_and_write_warnings()
        self._create_day_db_extract()
        self._network_temporal_from_week_db()
        self._create_gtfs_from_week_db()
        self._create_network_extracts()
        self._create_geojson_extracts()
        self._add_city_name_to_week_gtfs_db()
        self._write_stats()
        self._create_license_files()

    @flushed
    def _compute_stop_distances_osm_for_main_db(self):
        osm_file_path = "../../scratch/osm_data/planet-160502.osm.pbf"
        command = "java -jar -Xmx128G -Xms128G ../../gtfspy/java_routing/target/transit_osm_routing-1.0-SNAPSHOT-jar-with-dependencies.jar " \
                  " -u " + self.main_db_path + \
                  " -osm " + osm_file_path + \
                  " --tempDir ../../scratch/osm_data/"
        subprocess.run(command, shell=True, check=True)
        print("Removing unwalkable stop_distance_pairs")
        DELETE_UNWALKABLE_STOP_DISTANCE_PAIRS_SQL = "DELETE FROM stop_distances WHERE d_walk=-1"
        G = GTFS(self.main_db_path)
        G.conn.execute(DELETE_UNWALKABLE_STOP_DISTANCE_PAIRS_SQL)
        G.conn.commit()

    @flushed
    def _write_city_notes(self):
        with open(self.notes_fname, 'w') as f:
            to_write_str = "Original data downloaded on " + self.download_date + " from:\n"
            for feed in self.feeds:
                feed = str(feed).replace("_manually_expanded_gtfs", "")
                data = yaml.load(open("../gtfs-sources.yaml"))
                url = data['sites'][feed]['gtfs']
                if isinstance(url, dict):
                    for subfeed, path_to_gtfs in url.items():
                        to_write_str +=  "    " + feed + "," + subfeed + ": " + path_to_gtfs + "\n"
                else:
                    to_write_str += "    " + feed + ": " + url + "\n"

            G = GTFS(self.week_db_path)
            timezone_name = G.get_timezone_name()
            timezone_str = G.get_timezone_string()
            to_write_str += "Extract timezone: " + timezone_name + " (" +timezone_str + ")\n"
            to_write_str += CITY_ID_TO_NOTES_STR[self.city_id]
            print(to_write_str)
            f.write(to_write_str)

    @flushed
    def _add_city_name_to_week_gtfs_db(self):
        g = GTFS(self.week_db_path)
        g.meta['name'] = self.name

    @flushed
    def create_thumbnail_for_web(self):
        from gtfspy.mapviz import plot_route_network_thumbnail
        ax = plot_route_network_thumbnail(GTFS(self.week_db_path), map_style="dark_all")
        ax.figure.savefig(os.path.join(THUMBNAIL_DIR, self.city_id + ".jpg"))
        ax.figure.savefig(self.thumbnail_path)

    @flushed
    def assert_contents_exist(self, include_zip=False):
        files_required = ["network_combined.csv",
                          "network_nodes.csv",
                          "network_walk.csv",
                          "sections.geojson",
                          "stops.geojson",
                          "week.sqlite",
                          "network_temporal_day.csv",
                          "network_temporal_week.csv",
                          "routes.geojson",
                          "stats.csv",
                          "week.gtfs.zip",
                          "network_bus.csv",  # all cities we deal with should have buses
                          "license.txt",
                          "notes.txt",
                          "thumbnail.jpg"
                          ]
        if include_zip:
            files_required.append(self.city_id + ".zip")
        for file_required in files_required:
            assert os.path.exists(os.path.join(self.output_directory,
                                               file_required)), "File " + file_required + " missing from the output directory"
        return SUCCESS

    @flushed
    def deploy_to_transportnetorks_cs_aalto(self):
        assert self.publishable, "Feed " + self.city_id + " is not marked as publishable (1) according to to_publish.csv"
        server_dir_base_name = "/srv/transit/data/city_extracts/"
        server_dir_name = "/srv/transit/data/city_extracts/" + self.city_id
        cmd = 'ssh -t transportnetworks "mkdir -p ' + server_dir_name + '"'
        subprocess.run(cmd, shell=True, check=True)
        cmd = "rsync -avz --progress " + self.week_db_path + " transportnetworks:" + server_dir_name + "/week.sqlite"
        subprocess.run(cmd, shell=True, check=True)
        cmd = "rsync -avz --progress " + self.stats_fname + " transportnetworks:" + server_dir_name + "/stats.csv"
        subprocess.run(cmd, shell=True, check=True)
        cmd = "rsync -avz --progress " + self.thumbnail_path + " transportnetworks:" + server_dir_name + "/thumbnail.jpg"
        subprocess.run(cmd, shell=True, check=True)
        cmd = "rsync -avz --progress " + self.zip_file_name + " transportnetworks:" + server_dir_base_name
        subprocess.run(cmd, shell=True, check=True)

    @flushed
    def _write_stats(self):
        G = GTFS(self.day_db_path)
        net = combined_stop_to_stop_transit_network(G)
        sections = net.edges(data=True)
        n_links = len(sections)
        section_lengths = []
        vehicle_kilometers_per_section = []
        for from_I, to_I, data in sections:
            section_lengths.append(data['d'])
            vehicle_kilometers_per_section.append(data['n_vehicles'] * data['d'] / 1000.)

        stats = {"n_stops": len(G.stops(require_reference_in_stop_times=True)),
                 "n_connections": len(G.get_transit_events()),
                 "n_links": n_links,
                 "network_length_m": sum(section_lengths),
                 "link_distance_avg_m": int(sum(section_lengths) / len(section_lengths)),
                 "vehicle_kilometers": sum(vehicle_kilometers_per_section),
                 "buffer_center_lat": self.lat,
                 "buffer_center_lon": self.lon,
                 "buffer_radius_km": self.buffer_distance,
                 "extract_start_date": self.get_weekly_extract_start_date().strftime("%Y-%m-%d")
                 }
        self.__verify_stats(stats)
        df = pandas.DataFrame.from_dict({key:[value] for key, value in stats.items()})
        df.to_csv(self.stats_fname, sep=";", columns=list(sorted(stats.keys())), index=False)

    @flushed
    def __verify_stats(self, stats):
        keys_to_type = {
            "n_stops": int,
            "n_connections": int,
            "n_links": int,
            "network_length_m": int, # The sum of all links' (excluding walk) great circle distances, expressed in meters. \\
            "link_distance_avg_m": int,
            "vehicle_kilometers": float,
            "buffer_radius_km": (int, float),
            "buffer_center_lat": float,   # Latitude used for the center of filtering
            "buffer_center_lon": float,    # Longitude used for the center of filtering
            "extract_start_date": str
        }
        for key, key_type in keys_to_type.items():
            assert key in stats, "key " + key + " is missing"
            assert isinstance(stats[key], key_type), "value of key " + key + " is of wrong type " + str(stats[key]) + ", " + str(key_type)

    @flushed
    def _create_network_extracts(self):
        self._static_networks_from_day_db()
        self._network_temporal_from_day_db()
        self._combined_static_network_from_day_db()
        self._node_info_from_day_db()

    @flushed
    def import_original_feeds_into_raw_db(self):
        if not os.path.isfile(self.raw_db_path):
            subfeed_paths = self._get_subfeed_paths()
            print("Importing feeds " + " ".join(subfeed_paths))
            command = ' '.join(['python', '../../gtfspy/gtfspy/import_gtfs.py', 'import-multiple', ' '.join(subfeed_paths),
                                self.raw_db_path])
            subprocess.run(command, shell=True, check=True)
        else:
            print("Feed already imported, proceeding ...")
        return SUCCESS

    @flushed
    def _aggregate_stops_with_same_location(self):
        G = GTFS(self.raw_db_path)
        aggregate_stops_spatially(G, threshold_meters=1)

    @flushed
    def _main_db_extract(self):
        """
        Filter the raw database spatially (according to initialization parameters)
        and consider also
        """
        if os.path.isfile(self.main_db_path):
            os.remove(self.main_db_path)

        start_date, end_date = self.find_overlapping_calendar_span()
        print("Producing main extract")
        fe = filter.FilterExtract(
            GTFS(self.raw_db_path),
            self.main_db_path,
            buffer_distance_km=self.buffer_distance,
            buffer_lat=self.lat,
            buffer_lon=self.lon,
            update_metadata=True,
            start_date=start_date,
            end_date=end_date)
        fe.create_filtered_copy()

    @flushed
    def _create_day_db_extract(self):
        self.__create_temporal_extract_from_main_db(1, self.day_db_path)

    @flushed
    def _create_week_db_extract(self):
        self.__create_temporal_extract_from_main_db(7, self.week_db_path)

    @flushed
    def _static_networks_from_day_db(self):
        G = GTFS(self.day_db_path)
        exports.write_static_networks(G, self.output_directory, fmt="csv")

    @flushed
    def _combined_static_network_from_day_db(self):
        G = GTFS(self.day_db_path)
        exports.write_combined_transit_stop_to_stop_network(G, self.network_combined_fname, fmt="csv")

    @flushed
    def _node_info_from_day_db(self):
        exports.write_nodes(GTFS(self.day_db_path),
                            self.network_node_info_fname,
                            fields=['stop_I', 'lat', 'lon', 'name'])

    @flushed
    def _network_temporal_from_day_db(self):
        exports.write_temporal_network(GTFS(self.day_db_path), self.temporal_network_fname)

    @flushed
    def _network_temporal_from_week_db(self):
        exports.write_temporal_network(GTFS(self.week_db_path), self.temporal_network_week_fname)


    @flushed
    def _validate_raw_db_and_write_warnings(self):
        # import validator is run on the imported feed
        subfeed_paths = self._get_subfeed_paths()
        warnings_container = import_validator.ImportValidator(subfeed_paths, self.raw_db_path).validate_and_get_warnings()

        with open(self.raw_import_warnings_summary_fname, "w") as f:
            warnings_container.write_summary(f)
        with open(self.raw_import_warnings_details_fname, "w") as f:
            warnings_container.write_details(f)

    @flushed
    def _write_main_db_validation_warnings(self):
        # timetable validator is run on the filtered feed
        tv = timetable_validator.TimetableValidator(self.main_db_path, {'lat': self.lat,
                                                                        "lon": self.lon,
                                                                        "buffer_distance": self.buffer_distance})
        warnings_container = tv.validate_and_get_warnings()
        with open(self.main_db_timetable_warnings_summary_fname, "w") as f:
            warnings_container.write_summary(f)
        with open(self.main_db_timetable_warnings_details_fname, "w") as f:
            warnings_container.write_details(f)

    @flushed
    def _validate_week_db_and_write_warnings(self):
        # timetable validator is run on the filtered feed
        tv = timetable_validator.TimetableValidator(self.week_db_path, {'lat': self.lat,
                                                                        "lon": self.lon,
                                                                        "buffer_distance": self.buffer_distance})
        warnings_container = tv.validate_and_get_warnings()
        with open(self.week_db_timetable_warnings_summary_fname, "w") as f:
            warnings_container.write_summary(f)
        with open(self.week_db_timetable_warnings_details_fname, "w") as f:
            warnings_container.write_details(f)

    @flushed
    def _create_gtfs_from_week_db(self):
        if not os.path.exists(self.week_gtfs_path):
            week_db = GTFS(self.week_db_path)
            exports.write_gtfs(week_db, self.week_gtfs_path)

    @flushed
    def _create_geojson_extracts(self):
        day_gtfs = GTFS(self.day_db_path)
        exports.write_routes_geojson(day_gtfs, self.routes_geojson_fname)
        exports.write_sections_geojson(day_gtfs, self.sections_geojson_fname)
        exports.write_stops_geojson(day_gtfs, self.stops_geojson_fname)

    @flushed
    def _correct_coordinates_for_raw_db(self):
        g = GTFS(self.raw_db_path)
        df = self.coordinate_corrections
        for feed in self.feeds:
            feed_df = df.loc[df["feed"] == feed]
            print("Updating", len(feed_df.index), "known stop coordinate errors")
            g.update_stop_coordinates(feed_df)

    @flushed
    def _correct_arrival_times_for_raw_db(self):
        """
        Some feeds have had incorrect arrival and/or departure times, where
        e.g. p0.dep_time_ds = p1.arr_time_ds =/= p1.dep_time_ds = p2.arr_time_ds etc.
        If this has been done, there are long waits at stops, while traveling between stops takes zero time.
        """
        g = GTFS(self.raw_db_path)
        g.execute_custom_query("""UPDATE stop_times SET arr_time_ds = dep_time_ds
                                    WHERE EXISTS (
                                        SELECT * FROM
                                            (SELECT st2.trip_I AS trip_I, st2.seq AS seq FROM
                                                (SELECT stop_I, seq, trip_I, arr_time_ds,  dep_time_ds,
                                                 dep_time_ds - arr_time_ds AS wait_duration FROM stop_times) st1,
                                                (SELECT stop_I, seq, trip_I, arr_time_ds,  dep_time_ds,
                                                 dep_time_ds - arr_time_ds AS wait_duration FROM stop_times) st2
                                                    WHERE st1.trip_I = st2.trip_I AND st1.seq+1 = st2.seq
                                                        AND st1.dep_time_ds >= st2.arr_time_ds AND NOT st1.wait_duration = 0
                                                        AND NOT st2.wait_duration = 0)
                                            stop_pairs
                                        WHERE stop_times.trip_I=stop_pairs.trip_I AND stop_times.seq=stop_pairs.seq)""")
        g.conn.commit()

    @flushed
    def create_zip(self):
        self.assert_contents_exist(include_zip=False)
        if os.path.exists(self.zip_file_name):
            os.remove(self.zip_file_name)
        all_files = [os.path.join(self.output_directory, f) for f in listdir(self.output_directory)
                     if (((ExtractPipeline.TEMP_FILE_PREFIX not in f) and ("network_temporal.csv" not in f) and ("tmp-" not in f) and ("warnings" not in f)) or "week_db_timetable_warnings_summary.log" in f)]
        with ZipFile(self.zip_file_name, 'w', compression=zipfile.ZIP_DEFLATED) as cityzip:
            for path_to_file in all_files:
                print(path_to_file)
                cityzip.write(path_to_file, self.city_id + "/" + os.path.basename(path_to_file))

    @flushed
    def _get_subfeed_paths(self):
        """
        Walks trough the folders of the input feeds and returns the paths to the relevant GTFS zips (?)
        """
        subfeed_paths = FeedManager().get_subfeed_paths(self.feeds, self.download_date)
        if not len(subfeed_paths) > 0:
            raise Exception('No subfeeds found')
        else:
            print(str(len(subfeed_paths)) + ' subfeed(s) found for ' + self.city_id + " " + self.download_date)
            return subfeed_paths

    @flushed
    def find_overlapping_calendar_span(self):
        """
        Checks for the earliest end date and latest start date to assert that all feeds are overlapping
        :return:
        """
        from gtfspy.util import source_csv_to_pandas
        start_dates = []
        end_dates = []
        subfeed_start_end_dict_for_logging = {}
        for subfeed in self._get_subfeed_paths():
            start = float('inf')
            end = -float('inf')
            for table, [start_date_col, end_date_col] in zip(['calendar', 'calendar_dates'],
                                                             [['start_date', 'end_date'], ['date', 'date']]):
                # for args in [{"sep": '\s*,\s*'}, {'engine': 'python'}]:
                #         print(args)
                #     elif attempt == 1:
                #         args["engine"] ='python']
                df = source_csv_to_pandas(subfeed, table)
                if not df.empty:
                    start_df = df[start_date_col].astype(int).min()
                    if start_df < start:
                        start = start_df
                    end_df = df[end_date_col].astype(int).max()
                    if end_df > end:
                        end = end_df

            start_dates.append(start)
            end_dates.append(end)
            subfeed_start_end_dict_for_logging[subfeed] = [start, end]

        if max(start_dates) > min(end_dates):
            for key, value in subfeed_start_end_dict_for_logging.items():
                print('subfeed: ' + str(key) + ' has start date: ' + str(value[0]) + ' and end date: ' + str(value[1]))
            raise Exception('Calendars of ' + self.city_id + ' are not compatible: '
                                                          'the latest start date of all feeds '
                                                          'is before the earliest end date of all feeds')
        overlapping_start_date = util.to_date_string(max(start_dates))
        overlapping_end_date = util.to_date_string(min(end_dates))
        print('overlap start date: ' + overlapping_start_date + ' , overlap end date: ' + overlapping_end_date)
        return overlapping_start_date, overlapping_end_date

    def plot_weekly_extract_start_and_download_dates(self, given_axes=None):
        main_G = GTFS(self.main_db_path)
        assert isinstance(main_G, GTFS)
        day_extract_date_start = self.get_weekly_extract_start_date()
        print("Weekly extract start date: " + str(day_extract_date_start))
        print("Download date: " + str(self.download_date))
        from gtfspy.plots import plot_trip_counts_per_day
        ax = plot_trip_counts_per_day(main_G,
                                      highlight_dates=[day_extract_date_start, self.download_date],
                                      highlight_date_labels=["Week extract start date", "Source data download date"],
                                      ax=given_axes)
        ax.set_title(self.city_id.capitalize())
        ax.set_ylim([0, ax.get_ylim()[1] * 1.1])
        if given_axes:
            return ax.figure, ax
        else:
            ax.figure.savefig(self.weekly_extract_dates_plot_fname)
            print("saved figure to " + self.weekly_extract_dates_plot_fname)

    @flushed
    def __create_temporal_extract_from_main_db(self, days, output_db_path):
        if os.path.isfile(output_db_path):
            os.remove(output_db_path)
        main_G = GTFS(self.main_db_path)
        assert isinstance(main_G, GTFS)
        day_extract_date_start = self.get_weekly_extract_start_date()
        start_date_ut = main_G.get_day_start_ut(day_extract_date_start)
        three_am_seconds = 3 * 3600
        fe = filter.FilterExtract(main_G,
                                  output_db_path,
                                  update_metadata=True,
                                  trip_earliest_start_time_ut=start_date_ut + three_am_seconds,  # inclusive
                                  trip_latest_start_time_ut=start_date_ut + three_am_seconds + days * 24 * 3600)  # exclusive
        fe.create_filtered_copy()

    def get_weekly_extract_start_date(self):
        """
        Returns
        -------
        datetime.datetime
        """
        print("Weekly extract start date")
        if isinstance(self.extract_start_date, str):
            assert(len(self.extract_start_date) == 10)
            print("Obtained from to_publish.csv")
            return datetime.datetime.strptime(self.extract_start_date, "%Y-%m-%d")
        else:
            main_G = GTFS(self.main_db_path)
            print("Automatically computed based on database")
            assert isinstance(main_G, GTFS)
            day_extract_date_start = main_G.get_weekly_extract_start_date()
            return day_extract_date_start

if __name__ == "__main__":
    main()
