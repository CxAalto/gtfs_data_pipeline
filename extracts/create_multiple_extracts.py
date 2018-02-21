import os
import subprocess

from extract_pipeline import ExtractPipeline
from read_to_publish_csv import to_publish_generator

"""
This script acts as a parent process when importing multiple feeds in one go.
"""

ALL_CITIES = ["adelaide", "antofagasta", "athens", "belfast",
              "berlin", "bordeaux", "brisbane", "canberra", "detroit", "dublin", "kuopio", "lisbon", "luxembourg", "melbourne", "grenoble",
              "nantes", "palermo", "prague", "paris", "rennes", "rome", "sydney",
              "toulouse", "turku", "venice", "winnipeg", "helsinki"]

def main():

    cities_to_import = ALL_CITIES
    buffer_by_line = True
    
    commands = ["clear", "full", "thumbnail", "deploy_to_server"]

    print("Cities to import: ", cities_to_import)
    print("Commands to run: " , commands)

    for command in commands:
        logfile_path = get_logfile_base(command)
        for city_id in cities_to_import:
            if command == "extract_start_date":
                print_dates_for_a_city(city_id)
                continue
            elif command == "copy_from_hammer":
                print(city_id)
                copy_from_hammer(city_id)
                continue
            # standard process
            with open(logfile_path + "_" + city_id + ".txt", 'w', buffer_by_line) as logfile:
                p = subprocess.Popen(['python', 'extract_pipeline.py', command, str(city_id)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for line in iter(p.stdout.readline, b''):
                    logfile.write(str(line) + "\n")
                    print(str(line))


def print_dates_for_a_city(city):
    from matplotlib import pyplot as plt
    for to_publish_tuple, feeds in list(to_publish_generator()):
        if to_publish_tuple.id == city:
            try:
                pipeline = ExtractPipeline(to_publish_tuple, feeds)
                pipeline.plot_weekly_extract_start_and_download_dates()
            except Exception as e:
                print("Something went wrong with city " + city + " :")
                print(str(e))
    plt.show()

def copy_from_hammer(city_id):
    copy_dir_name = os.path.join("copies_from_hammer", city_id)
    os.makedirs(copy_dir_name, exist_ok=True)
    copy_command = "rsync -avz --progress hammer:/m/cs/scratch/networks/rmkujala/transit/to_publish/" + city_id + "/* " + copy_dir_name + "/"
    print(copy_command)
    subprocess.call(copy_command, shell=True)

def get_logfile_base(command):
    try:
        assert os.path.exists("import_logs")
    except AssertionError:
        os.mkdir("import_logs")

    logfile_path_base = 'import_logs/log_{i}'
    i=0
    while os.path.exists(logfile_path_base.format(i=i)):
        i += 1
    logfile_path = logfile_path_base.format(i=i)
    with open(logfile_path, 'w') as logfile:
        logfile.write(command)
    subprocess.call(["touch", logfile_path])
    print("Logfile bases: " + logfile_path)
    return logfile_path

if __name__ == "__main__":
    main()

