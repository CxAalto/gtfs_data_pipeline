import os
import subprocess
from read_to_publish_csv import get_to_publish_csv

"""
This short script has one simple task: to act as a parent process when importing multiple feeds in one go.
"""

ALL_CITIES = ["detroit", "lisbon", "luxembourg", "prague", "adelaide", "antofagasta", "athens", "belfast",
              "berlin", "bilbao", "bordeaux", "brisbane", "canberra", "dublin", "melbourne", "grenoble",
              "nantes", "palermo", "mallorca", "paris", "rennes", "rio_de_janeiro", "rome", "sydney",
              "toulouse", "valencia", "valparaiso", "venice", "winnipeg", "helsinki"]
def main():
    # cities_to_import = [city for city in all_cities if city not in cities_to_neglect]

    # start_from = "rio_de_janeiro"
    # cities_to_import = all_cities[all_cities.index(start_from):]
    
    cities_to_import = ALL_CITIES # ["melbourne"]
    commands = ["clear", "full"]

    print("Cities to import: ", cities_to_import)
    logfile_path = get_logfile_base()
    buffer_by_line = 1
    for command in commands:
        for city_id in cities_to_import:
            print(city_id)
            # copy_from_hammer(city_id)
            # continue
            with open(logfile_path + "_" + city_id + ".txt", 'w', buffer_by_line) as logfile:
                p = subprocess.Popen(['python', 'extract_pipeline.py', command, str(city_id)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                for line in iter(p.stdout.readline, b''):
                    logfile.write(str(line) + "\n")
                    print(str(line))

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
