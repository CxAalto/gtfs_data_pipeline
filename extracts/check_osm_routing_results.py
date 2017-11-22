"""
Checking how much the results between straight-line routing and the one using GraphHopper differ.
"""
import os
import re

from gtfspy.gtfs import GTFS

from matplotlib import pyplot as plt

from create_multiple_extracts import ALL_CITIES

for city_id in ALL_CITIES:
    copy_dir_name = os.path.join("copies_from_hammer", city_id)
    try:
        directory_listing = os.listdir(copy_dir_name)
    except FileNotFoundError as e:
        print(e)
        continue

    date_regexp = re.compile("....-..-..")
    for directory_candidate in directory_listing:
        if date_regexp.match(directory_candidate) is not None:
            sqlite_fname = os.path.join(copy_dir_name, directory_candidate, "week.sqlite")

            if not os.path.exists(sqlite_fname):
                print(sqlite_fname + " does not exist!")
                continue
            G = GTFS(sqlite_fname)
            stop_distances_df = G.get_table("stop_distances")

            print(len(stop_distances_df))

            stop_distances_df = G.get_table("stop_distances")
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.scatter(stop_distances_df['d'], stop_distances_df['d_walk'], s=1)
            ax.set_title(city_id)
            plt.show()

