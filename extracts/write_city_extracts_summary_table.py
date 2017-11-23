import os

import pandas

from create_multiple_extracts import ALL_CITIES
from extract_pipeline import ExtractPipeline
from gtfspy.gtfs import GTFS
from licenses.adapt_licenses import CITY_ID_TO_LICENSE_TYPE
from read_to_publish_csv import get_to_publish_csv, get_feeds_from_to_publish_tuple
from settings import TO_PUBLISH_ROOT_OUTPUT_DIR

cities = []
for city in sorted(ALL_CITIES):
    to_publish_csv = get_to_publish_csv()
    city_data = to_publish_csv[to_publish_csv["id"] == city].iloc[0]
    city_data_dict = dict()
    city_data_dict["name"] = city_data["name"]
    city_data_dict["lat"] = city_data.lat
    city_data_dict["lon"] = city_data.lon
    city_data_dict["buffer_radius_km"] = city_data.buffer
    city_data_dict["download_date"] = city_data.download_date
    license = CITY_ID_TO_LICENSE_TYPE[city]
    license = license.replace("CC", "CC BY")
    license = license.replace("_", " ")
    city_data_dict["license"] =license
    feeds = get_feeds_from_to_publish_tuple(city_data)
    pipeline = ExtractPipeline(city_data, feeds)
    try:
        day_G = GTFS(pipeline.day_db_path)
        trip_counts_per_day = day_G.get_trip_counts_per_day()
        assert len(trip_counts_per_day) == 1
        city_data_dict["day_extract_date"] = trip_counts_per_day.iloc[0]['date']
    except FileNotFoundError as e:
        print("File " + pipeline.day_db_path + " was not found")
        city_data_dict["day_extract_date"] = "NaN"
    cities.append(city_data_dict)


with open(os.path.join(TO_PUBLISH_ROOT_OUTPUT_DIR, "city_summary_table.tex"), "w") as f:
    print(pandas.DataFrame(cities)
          .to_latex(index=False,
                    columns=["name", "lat", "lon", "buffer_radius_km",
                             "download_date", "day_extract_date", "license"]))

