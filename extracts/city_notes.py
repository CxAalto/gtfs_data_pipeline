_DATA_OK = "The data should cover all relevant modes of intra-city public transport."
_DATA_OK_BUT = "The data should cover all relevant modes of intra-city public transport, but "
_DATA_OK_EXCEPT = "The data should cover all relevant modes of intra-city public transport, except for"
_TODO_STR = "!!!!!!!!!!!!!!!!This feed needs to be checked still!!!!!!!!!!!!!"
_MIN_TRANSFER_TIME_STOP_PAIRS_NOTE = "There are some stop pairs for which minimum transfer time is defined, although they are more than 1000 meters apart. Thus walking distances are also computed between these stops."




CITY_ID_TO_NOTES_STR = {
    "adelaide": _DATA_OK,
    "antofagasta": _DATA_OK_BUT + " in Antofagasta there are also \"collectivos\" that operate on regular routes but are not centrally coordinated.",
    "athens": "Commuter trains are missing.",
    "belfast": "Commuter trains are missing.",
    "berlin": _DATA_OK,
    "bordeaux": "Commuter trains and regional buses are missing.",
    "brisbane": _DATA_OK,
    "canberra": _DATA_OK,
    "detroit": "Only bus services in the operated by the Detroit Department of Transportation are included.\n"
               " Services operated by the Suburban Mobility Authority for Regional Transportation (SMART) are not included.\n" +
               "'People Mover'- monorail service in the city center is not included.\n" +
               " Public transport of the neighboring city of Windsor (Ontario, Canada) is not included.",
    "dublin": _DATA_OK,
    "grenoble": "Commuter trains and regional buses are missing.",
    "helsinki": _DATA_OK,
    "kuopio": _DATA_OK,
    "lisbon": "Trams are missing. Services operated by Scotturb are missing (municipalities of Sintra and Cascais).",
    "luxembourg": _DATA_OK + "\n" + _MIN_TRANSFER_TIME_STOP_PAIRS_NOTE,
    "melbourne": _DATA_OK,
    "nantes": "Commuter trains are missing.",
    "palermo": "Commuter trains are missing. Note that after the time-span covered by the data, four tram lines have been installed in Palermo.",
    "paris": _DATA_OK,
    "prague": "Commuter trains are missing.",
    "rennes": "Commuter trains are missing.",
    "rome": _DATA_OK,
    "turku": _DATA_OK,
    "sydney": _DATA_OK,
    "toulouse": "Commuter trains are missing.",
    # "valencia": "Only bus traffic is included. Data for metros is not available.",
    # "valparaiso": "The feed does not include funiculars.\n"
    #               "Note that in addition to public transport, in Valparaiso there are also `collectivos` (shared taxis).\n"
    #              "The feed end dates in original data were tens of years ahead (in calendar.txt). The end dates were shortened manually before filtering.",
    "venice": "Commuter trains are missing.",
    "winnipeg": _DATA_OK,
}
