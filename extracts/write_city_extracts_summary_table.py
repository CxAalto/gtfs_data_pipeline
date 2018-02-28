import os

import pandas

from create_multiple_extracts import ALL_CITIES
from extract_pipeline import ExtractPipeline
from gtfspy.gtfs import GTFS
from gtfspy.networks import combined_stop_to_stop_transit_network
from licenses.adapt_licenses import CITY_ID_TO_LICENSE_TYPE
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple
from settings import TO_PUBLISH_ROOT_OUTPUT_DIR

import pickle

pickle_cache_file = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR,"_latex_summary_table_cache.pickle")

try:
    print("Trying to fetch city data from cache...")
    assert False
    cities = pickle.load(open(pickle_cache_file, 'rb'))
    print("It worked!")
except:
    print("That did not work out, recomputing city data:")
    cities = []
    for city in sorted(ALL_CITIES):
        print("Obtaining summary table data for " + city)
        to_publish_csv = get_to_publish_csv()
        city_data = to_publish_csv[to_publish_csv["id"] == city].iloc[0]
        city_data_dict = dict()
        city_data_dict["City"] = city_data["name"]
        city_data_dict["Country"] = city_data["country"]
        city_data_dict["Latitude"] = city_data.lat
        city_data_dict["Longitude"] = city_data.lon
        city_data_dict["Buffer radius (km)"] = int(city_data.buffer)
        city_data_dict["Download date"] = city_data.download_date
        license = CITY_ID_TO_LICENSE_TYPE[city]
        license = license.replace("CC", "CC BY")
        license = license.replace("CC BY0", "CC0")
        license = license.replace("_", " ")
        city_data_dict["License"] =license
        feeds = get_feeds_from_to_publish_tuple(city_data)
        pipeline = ExtractPipeline(city_data, feeds)
        try:
            day_G = GTFS(pipeline.day_db_path)
            trip_counts_per_day = day_G.get_trip_counts_per_day()
            print(trip_counts_per_day)
            assert len(trip_counts_per_day) <= 3
            city_data_dict["Extract date"] = str(trip_counts_per_day.loc[trip_counts_per_day['trip_counts'] == max(trip_counts_per_day['trip_counts'])].iloc[0]['date'])
            print(city_data_dict["Extract date"].replace(" 00:00:00", ""))
            city_data_dict["n_stops"] = len(day_G.stops(require_reference_in_stop_times=True))
            city_data_dict["n_connections"] = len(day_G.get_transit_events())
            n_links = len(combined_stop_to_stop_transit_network(day_G).edges(data=True))
            city_data_dict["n_links"] = int(n_links)
        except FileNotFoundError as e:
            print("File " + pipeline.day_db_path + " was not found")
            city_data_dict["Extract date"] = "NaN"
        cities.append(city_data_dict)
    pickle.dump(cities, open(pickle_cache_file, 'wb'), -1)


def spaces(x):
    try:
        num_as_str_reversed = str(int(x))[::-1]
        num_with_spaces = ',\\'.join(num_as_str_reversed[i:i + 3] for i in range(0, len(num_as_str_reversed), 3))
        return num_with_spaces[::-1]
    except ValueError:
        return "NaN"





fname_stats = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "city_stats_summary_table.tex")
with open(fname_stats, "w") as f:
    print(fname_stats)
    pandas.DataFrame(cities).to_latex(
        buf=f,
        formatters={"n_stops": spaces, "n_connections": spaces, "n_links": spaces},
        index=False,
        columns=["City", "Country", "n_stops", "n_links", "n_connections", "License"],
        float_format='%.0f'
    )

fname_details = os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "city_details_table.tex")
with open(fname_details, "w") as f:
    print(fname_details)
    pandas.DataFrame(cities).to_latex(
        buf=f,
        columns = ["City", "Latitude", "Longitude", "Buffer radius (km)", "Download date", "Extract date"],
        float_format='%.4f',
        index=False
    )
