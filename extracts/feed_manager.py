import os

import yaml
import pandas
from gtfspy import util

from read_to_publish_csv import to_publish_generator
from settings import RAW_DATA_DIR, GTFS_ZIPFILE_BASENAME


class FeedManager(object):
    """
    Reads the file structures, and tells what feeds are available, and for which time perioids.
    """

    def __init__(self, raw_data_dir=RAW_DATA_DIR):
        self.raw_data_dir = raw_data_dir

    def available_dates(self, feed_availability_path=None):
        """
        Browses trough all rawgtfs folders to check which gtfs files are available (ignoring empty zip files).

        Parameters
        ----------
        feed_availability_path: str
            path to the csv report (created by write_complete_feeds_status)

        Return
        ------
        grouped: pandas.DataFrame
        """
        if feed_availability_path is None:
            feed_availability_path = os.path.join(RAW_DATA_DIR + "feed_availability.csv")

        feed_list = []
        print("Browsing feeds...")
        for to_publish_tuple, feeds in to_publish_generator():
            for feed in feeds:
                for download_date, sub_feed, filepath in self._date_filter_dir(feed):
                    feed_list.append([to_publish_tuple.id, feed, sub_feed, download_date, filepath])
        # create pandas dataframe
        n_feeds = len(feed_list)
        if n_feeds == 0:
            print("No feeds found terminating...")
            return
        print(str(n_feeds), " feeds found")
        df = pandas.DataFrame(feed_list, columns=(u'city', u'feed', u'subfeed', u'download_date', u'filepath'))
        # sort values based on download_date
        df = df.sort_values(by=u'download_date', axis=0, ascending=False)
        print("Checking zip validity...")
        for i, row in enumerate(df.itertuples()):
            print('\rFeed ', str(i+1), " of ", str(n_feeds), end='')
            df.set_value(row.Index, row.download_date, util.corrupted_zip(row.filepath))

        df = df.drop([u'download_date', u'filepath'], 1)
        # select first row (the available date) grouped by city, feed, subfeed
        grouped = df.groupby(by=[u'city', u'feed', u'subfeed'], axis=0).first().reset_index()
        print("\nWriting file...")
        grouped.to_csv(path_or_buf=feed_availability_path)
        print("Report saved at ", feed_availability_path, ", Done!")
        return grouped

    def write_complete_feeds_status(self, complete_feeds_path=None):
        """
        Checks if all subfeeds of a feed are available at the available download dates.
        Writes results in a .csv file.

        Parameters
        ----------
        complete_feeds_path: str, optional
            where to write the results
        """
        if complete_feeds_path is None:
            complete_feeds_path = os.path.join(os.path.join(RAW_DATA_DIR + "/write_complete_feeds_status.csv"))

        available_subfeeds = self.available_dates()  # pandas dataframe
        feed_dict = self._all_required_subfeeds()  # dict
        new_df = available_subfeeds.drop([u'feed', u'subfeed'], axis=1)
        new_df = new_df.groupby(by=[u'city']).first().reset_index()

        for city, subfeeds in feed_dict.items():

            selection = available_subfeeds.loc[available_subfeeds[u'city'] == city]
            selection = selection.loc[selection[u'subfeed'].isin(subfeeds)]
            dates = selection.drop([u'city', u'feed', u'subfeed'], axis=1)
            for column in list(dates.columns.values):
                if all(item == 'ok' for item in selection[column].tolist()):

                    new_df.set_value(new_df[new_df[u'city'] == city].index.tolist(), column, 'ok')
                else:
                    n = sum(item == 'error' or pandas.isnull(item) for item in selection[column].tolist())
                    new_df.set_value(new_df[new_df[u'city'] == city].index.tolist(), column, str(n) + ' missing')

        new_df.reset_index().to_csv(path_or_buf=complete_feeds_path)

    def _all_required_subfeeds(self):
        """
        For each city, merges the required feeds in to_publish.csv with the active subfeeds in gtfs-sources.yaml
        Returns
        -------
            feed_dict dict key = city, value = list of subfeeds
        """

        subfeeds = self._get_subfeeds_from_yaml()
        feed_dict = {}
        for to_publish_tuple, feeds in to_publish_generator():
            city = to_publish_tuple.id
            subfeed_list = []
            for feed in feeds:
                try:
                    subfeed_list += subfeeds[feed]
                except KeyError as e:
                    print('missing feed ' + feed + ' ignored')
            feed_dict[city] = subfeed_list
        return feed_dict

    def _get_subfeeds_from_yaml(self, fname=None):
        """
        Load YAML file describing the original gtfs sources into a dictionary mapping
        each city (or a country-wise feed) into a list of subfeeds.
        If there is only one subfeed, its name will be main.

        Returns
        -------
        location_to_subfeeds: dict
            maps each city to a list of subfeeds (name)

        """
        if fname is None:
            this_dir = os.path.dirname(os.path.realpath(__file__))
            fname = os.path.join(this_dir, "../gtfs-sources.yaml")

        data = yaml.load(open(fname))
        sites = data['sites']
        location_to_subfeeds = {}
        for feed_name, data in sites.items():
            if data is None:
                continue
            # if name not in ('test', 'test2'): continue
            if isinstance(data['gtfs'], dict):
                subfeeds = []
                for subfeed_name, url in data['gtfs'].items():
                    subfeeds.append(subfeed_name)

                location_to_subfeeds[feed_name] = subfeeds
            else:
                location_to_subfeeds[feed_name] = ['main']
        return location_to_subfeeds

    def _date_filter_dir(self, feed):
        """
        Generator returning all download_dates and filepaths for all subfeeds of a feed.

        Parameters
        ----------
        feed: str

        Yields
        ------
        download_date: ?
        sub_feed: ?
        filepath: ?
        """
        for cur_dir, subdirs, files in os.walk(os.path.join(self.raw_data_dir, feed)):
            if GTFS_ZIPFILE_BASENAME in files:
                filepath = os.path.join(cur_dir, GTFS_ZIPFILE_BASENAME)
                sub_feed = os.path.split(os.path.normpath(cur_dir))[-1]
                download_date = os.path.basename(os.path.split(os.path.normpath(cur_dir))[-2])
                yield download_date, sub_feed, filepath

    def get_subfeed_paths(self, feeds, download_date):
        subfeed_paths = []
        for feed in feeds:
            basedir = os.path.join(RAW_DATA_DIR, feed, download_date)
            # print(basedir)
            for cur_dir, subdirs, files in os.walk(basedir):
                if GTFS_ZIPFILE_BASENAME in files:
                    subfeed_paths.append(cur_dir + "/" + GTFS_ZIPFILE_BASENAME)
        return subfeed_paths

