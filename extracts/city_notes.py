_DATA_OK = "The data should cover all relevant modes of intra-city public transport."
_DATA_OK_BUT = "The data should cover all relevant modes of intra-city public transport, but "
_DATA_OK_EXCEPT = "The data should cover all relevant modes of intra-city public transport, except for"
_TODO_STR = "!!!!!!!!!!!!!!!!This feed needs to be checked still!!!!!!!!!!!!!"
_MIN_TRANSFER_TIME_STOP_PAIRS_NOTE = "There are some stop pairs for which minimum transfer time is defined, although they are more than 1000 meters apart, and walking distances are also computed between these stops."

CITY_ID_TO_NOTES_STR = {
    "adelaide": _DATA_OK,
    "antofagasta": _DATA_OK_BUT + " in Antofagasta there are also \"collectivos\" "
                                     "that operate on regular routes but are not centrally coordinated.",
    "athens": "The data does not contain metro lines and the suburban railways.",
    "belfast": "The data does not contain railroad connections.",
    "berlin": _DATA_OK,
    "bordeaux": "The data does not contain regional bus and rail transport.",
    "brisbane": _DATA_OK + " Some long lines ('tendrils') spread far out from Brisbane.",
    "canberra": _DATA_OK,
    "detroit": "Only the bus services of the city center are included. " +
               "'People Mover'- monorail service in the city center is not included.",
    "dublin": _DATA_OK + " Some long lines ('tendrils') spread far out from Dublin.",
    "grenoble": _DATA_OK_BUT + " regional/long distance railways are not included.",
    "helsinki": _DATA_OK_BUT + " some long lines ('tendrils') spread far out from Helsinki.",
    "lisbon": _DATA_OK,
    "luxembourg": _TODO_STR + "\n" + _MIN_TRANSFER_TIME_STOP_PAIRS_NOTE,
    "mallorca": "The data is missing the inner city public transport!",
    "melbourne": _DATA_OK,
    "nantes": _DATA_OK,
    "palermo": _DATA_OK + " Note that after the time-span covered by the data, "
                             "four tram lines have been installed in Palermo.",
    "paris": _DATA_OK,
    "prague": _DATA_OK + " Long distance train stops and connections are not included.",
    "rennes": _DATA_OK_EXCEPT + " regional train connections.",
    "rio_de_janeiro":  "Only the bus network is covered, no trams, metros, ferries or trains are included",
    "rome": _DATA_OK,
    "sydney": _DATA_OK + " Some long lines ('tendrils') spread far out from Sidney." ,
    "toulouse": _DATA_OK_BUT + " regional/long distance railways are not included.",
    "valencia": "Only bus traffic is included. Data for metros is not available.",
    "venice": "Regional railroad connections are missing (in mainland Venice). Otherwise essential city information seems to be ",
    "winnipeg": _DATA_OK,
}