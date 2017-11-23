import os
import subprocess

from extract_pipeline import ExtractPipeline
from read_to_publish_csv import to_publish_generator

"""
This script acts as a parent process when importing multiple feeds in one go.
"""

ALL_CITIES = ["adelaide", "antofagasta", "athens", "belfast",
              "berlin", "bordeaux", "brisbane", "canberra", "detroit", "dublin", "lisbon", "luxembourg", "melbourne", "grenoble",
              "nantes", "palermo", "prague", "mallorca", "paris", "rennes", "rio_de_janeiro", "rome", "sydney",
              "toulouse", "valencia", "valparaiso", "venice", "winnipeg", "helsinki"]

def main():
    # cities_to_import = [city for city in all_cities if city not in cities_to_neglect]

    start_from = "bilbao"
    cities_to_import = ALL_CITIES[ALL_CITIES.index(start_from):]
    
    # cities_to_import = ALL_CITIES  # ["melbourne"]
    commands = ["extract_start_date"]  # "clear", "full"]

    print("Cities to import: ", cities_to_import)
    logfile_path = get_logfile_base()
    buffer_by_line = 1
    for command in commands:
        for city_id in cities_to_import:
            print_dates_for_a_city(city_id)
            # print(city_id)
            # copy_from_hammer(city_id)
            # continue
            # standard processes
            continue
            with open(logfile_path + "_" + city_id + ".txt", 'w', buffer_by_line) as logfile:
                p = subprocess.Popen(['python', 'extract_pipeline.py', command, str(city_id)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for line in iter(p.stdout.readline, b''):
                    logfile.write(str(line) + "\n")
                    print(str(line))


def print_dates_for_a_city(city):
    for to_publish_tuple, feeds in list(to_publish_generator()):
        if to_publish_tuple.id == city:
            try:
                pipeline = ExtractPipeline(to_publish_tuple, feeds)
                pipeline.plot_weekly_extract_start_and_download_dates()
            except:
                print("Something went wrong with city " + city)


def copy_from_hammer(city_id):
    copy_dir_name = os.path.join("copies_from_hammer", city_id)
    os.makedirs(copy_dir_name, exist_ok=True)
    copy_command = "rsync -avz hammer:/m/cs/scratch/networks/rmkujala/transit/to_publish/" + city_id + "/* " + copy_dir_name + "/"
    print(copy_command)
    subprocess.call(copy_command, shell=True)

def get_logfile_base():
    try:
        assert os.path.exists("import_logs")
    except AssertionError:
        os.mkdir("import_logs")

    logfile_path_base = 'import_logs/log_{i}'
    i=0
    while os.path.exists(logfile_path_base.format(i=i)):
        i += 1
    logfile_path = logfile_path_base.format(i=i)
    subprocess.call(["touch", logfile_path])
    print("Logfile bases: " + logfile_path)
    return logfile_path

if __name__ == "__main__":
    main()

