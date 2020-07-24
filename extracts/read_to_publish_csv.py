import pandas
from settings import PATH_TO_PUBLISH_CSV


def to_publish_generator():
    """
    Generator returning all rows from to_publish.csv

    Returns
    -------
    to_publish_tuple: tuple
        with fields (id,Name,buffer,feeds,download_date,lon,lat)
    feeds: list
    """
    to_publish_list = get_to_publish_df()
    for to_publish_tuple in to_publish_list.itertuples():
        # Which sub-feeds to publish?
        yield to_publish_tuple, get_feeds_from_to_publish_tuple(to_publish_tuple)


def get_feeds_from_to_publish_tuple(to_publish_tuple):
    if to_publish_tuple.feeds == "" or pandas.isnull(to_publish_tuple.feeds):
        # get all from this city/full feed
        return [to_publish_tuple.id]
    else:
        # city consists of multiple locations
        return to_publish_tuple.feeds.split(";")


def get_to_publish_df():
    """
    Returns
    -------
    pandas.DataFrame
    """

    dtypes = {"publishable": object,
              "license_files": str,
              "lat": float,
              "lon": float,
              "buffer": float,
              "feeds": str,
              "extract_start_date": str,
              "download_date": str}
    to_publish_list = pandas.read_csv(PATH_TO_PUBLISH_CSV, sep=",", keep_default_na=True, dtype=dtypes)
    to_publish_list.license_files.fillna("")
    return to_publish_list


if __name__ == "__main__":
    # testing
    for d in to_publish_generator():
        print(d)
        exit()
