import os
import subprocess

import pandas

from .original_authors import FEED_SLUG_TO_AUTHOR_STR

__THIS_DIR = os.path.dirname(os.path.realpath(__file__))

TO_PUBLISH_CSV_DF = pandas.read_csv(os.path.join(__THIS_DIR, "../", "to_publish.csv"), index_col="id")
DECONET_AUTHORS_STR = "Rainer Kujala, Christoffer Weckström and Richard Darst"


READY_LICENSES_DIR = os.path.join(__THIS_DIR, "ready_licenses/")

CITY_ID_TO_LICENSE_TYPE = {
    "detroit": "CC0",
    "lisbon": "CC0",
    "luxembourg": "CC0",
    "prague": "CC0",
    "adelaide": "CC_4.0",
    "antofagasta": "CC_NC_2.0",
    "athens": "CC_NC_4.0",
    "belfast": "ODBL_v1.0",
    "berlin": "CC_3.0_DE",
    "bilbao": "CC_4.0",
    "bordeaux": "ODBL_v1.0",
    "brisbane": "CC_3.0_AU",
    "canberra": "CC_4.0",
    "dublin": "CC_4.0",
    "grenoble": "ODBL_v1.0",
    "kuopio": "CC_4.0",
    "melbourne": "CC_4.0",
    "nantes":  "ODBL_v1.0_fr",
    "palermo": "CC_4.0",
    "paris": "ODBL_v1.0_fr",
    "rennes": "ODBL_v1.0",
    "rio_de_janeiro": "ODBL_v1.0",
    "rome": "CC_3.0_IT",
    "sydney": "CC_4.0",
    "toulouse": "ODBL_v1.0",
    "turku": "CC_4.0",
    "valencia": "CC_4.0",
    "valparaiso": "CC_NC_2.0",
    "venice": "CC_3.0_IT",
    "winnipeg": "PDDL",
    "helsinki": "CC_4.0"
}

LICENSE_TYPE_TO_LICENSE_URL = {
    "CC_NC_2.0": "<https://creativecommons.org/licenses/by-nc/2.0/>",
    "CC_4.0": "<https://creativecommons.org/licenses/by/4.0/>",
    "CC_NC_4.0": "<https://creativecommons.org/licenses/by-nc/4.0/>",
    "ODBL_v1.0": "<https://opendatacommons.org/licenses/odbl/1.0/>",
    "ODBL_v1.0_fr": "<https://opendatacommons.org/licenses/odbl/1.0/> (Original data was provided under the French translation, available at <http://vvlibri.org/fr/licence/odbl-10/legalcode/unofficial>)",
    "CC_3.0_DE": "<https://creativecommons.org/licenses/by/3.0/de/>",
    "CC_3.0_AU": "<https://creativecommons.org/licenses/by/3.0/au/>",
    "CC_3.0_IT": "<https://creativecommons.org/licenses/by/3.0/it/>",
    "PDDL": "<https://opendatacommons.org/licenses/pddl/1.0/>"
}

LICENSE_TYPE_TO_LICENSE_NAME = {
    "CC_NC_2.0": "Creative Commons Attribution-NonCommercial 2.0 Generic License",
    "CC_4.0":    "Creative Commons Attribution 4.0 International License",
    "CC_NC_4.0": "Creative Commons Attribution-NonCommercial 4.0 License",
    "ODBL_v1.0": "Open Database License (ODbL) v1.0",
    "ODBL_v1.0_fr": "Open Database License (ODbL) v1.0",
    "CC_3.0_DE": "Creative Commons \"Namensnennung 3.0 Deutschland\" (CC BY 3.0 DE) - License",
    "CC_3.0_AU": "Creative Commons Attribution 3.0 Australia (CC BY 3.0 AU) - License",
    "CC_3.0_IT": "Creative Commons \"Attribuzione 3.0 Italia\" (CC BY 3.0 IT) - License",
    "PDDL": "ODC Public Domain Dedication and Licence (PDDL)"
}

LICENSE_TYPE_TO_LEGAL_CODE_BASE_NAME = {
    "CC0": "cc0_1.0_legalcode.txt",
    "CC_4.0": "cc_by_4.0_legalcode.txt",
    "CC_NC_2.0": "cc_by_nc_2.0_legalcode.txt",
    "CC_NC_4.0": "cc_by_nc_4.0_legalcode.txt",
    "ODBL_v1.0": "odbl_v1.0_legalcode.txt",
    "ODBL_v1.0_fr": "odbl_v1.0_legalcode.txt",
    "CC_3.0_DE": "cc_by_3.0_de_legalcode.txt",
    "CC_3.0_AU": "cc_by_3.0_au_legalcode.txt",
    "CC_3.0_IT": "cc_by_3.0_it_legalcode.txt",
    "PDDL": "odc_pddl_legalcode.txt"
}


# CC0_LEGAL_CODE_BASE_NAME = "cc0_1.0_legalcode.txt"
# CC_BY_40_LEGAL_CODE_BASE_NAME = "cc_by_4.0_legalcode.txt"
# CC_BY_NC_20_LEGAL_CODE_BASE_NAME = "cc_by_nc_2.0_legalcode.txt"


def create_license_files(city_slug, city_license_output_dir=None):
    assert city_slug in CITY_ID_TO_LICENSE_TYPE
    if city_license_output_dir is None:
        city_license_output_dir = os.path.join(READY_LICENSES_DIR, city_slug)
    try:
        os.mkdir(city_license_output_dir)
    except FileExistsError:
        pass

    city_name = TO_PUBLISH_CSV_DF.loc[city_slug]["name"]
    extract_name = "\"" + city_name + " public transport extract\""
    city_license_fname = os.path.join(city_license_output_dir, "license.txt")
    feed_author_str = FEED_SLUG_TO_AUTHOR_STR[city_slug]
    license_type = CITY_ID_TO_LICENSE_TYPE[city_slug]
    LEGAL_CODE_BASE_NAME = LICENSE_TYPE_TO_LEGAL_CODE_BASE_NAME[license_type]

    if license_type == "CC0":
        command = "sed -e 's/WORKS_NAME/" + extract_name + "/g' -e 's/AUTHORS_NAME/" + DECONET_AUTHORS_STR + \
                "/g' " + os.path.join(__THIS_DIR, "license_cc0_base.txt") + " > " + city_license_fname
        subprocess.call(command, shell=True)
    else:
        with open(city_license_fname, "w") as f:
            f.write(get_license_text(license_type, extract_name, feed_author_str))

    # copy legal code
    subprocess.call(["cp", os.path.join(__THIS_DIR, "legal_codes/", LEGAL_CODE_BASE_NAME), os.path.join(city_license_output_dir, LEGAL_CODE_BASE_NAME)])

def get_license_text(license_type, extract_name, feed_authors):
    license_url = LICENSE_TYPE_TO_LICENSE_URL[license_type]
    license_name = LICENSE_TYPE_TO_LICENSE_NAME[license_type]
    license_text = "This work {extract_name}, is provided under {license_name}.\n" \
                   "The original public transport schedule data has been provided by {feed_authors} under the same license.\n" \
                   "You should have received a copy of the license along with this work. If not, please see {license_url}.\n" \
                   "The walking distances between stops have been computed based on information from OpenStreetMap (www.openstreetmap.org) which is licensed under the Open Data Commons Open Database License (https://opendatacommons.org/licenses/odbl/) by the OpenStreetMap Foundation.\n" \
                   "The adapted versions of the schedule data have been been created by {deconet_authors}.\n" \
                   "No warranties are given.\n" \
        .format(extract_name=extract_name,
                            license_url=license_url,
                            license_name=license_name,
                            feed_authors=feed_authors,
                            deconet_authors=DECONET_AUTHORS_STR)
    return license_text


def clean():
    subprocess.call(["rm", "-rf", READY_LICENSES_DIR])


if __name__ == "__main__":
    clean()
    subprocess.call("mkdir -p " + READY_LICENSES_DIR, shell=True)

    for city_slug in CITY_ID_TO_LICENSE_TYPE:
        print(city_slug)
        create_license_files(city_slug)

