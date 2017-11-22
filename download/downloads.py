"""
Manage downloading of GTFS files over multiple locations.

This file handles
- Reading in gtfs-sources.yaml that describes data sources
- Checking already-downloaded data
- Downloading data, if it is time to do so again

For running the weekly periodic download, use:

    python pipeline/downloads.py scrape

"""
import calendar
import datetime
import os
import sys
from urllib.request import FancyURLopener
import yaml
import time
from os.path import join
from gtfspy import util

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from settings import RAW_DATA_DIR_PARENT_DIR

# data layout:
#
# - $location is the standard location slug.
# - $date is the date, in YYYY-MM-DD format
# - $part is the partition-slug if data comes in several files.
#   Is "main" if only one partition.
#
# The following are some of the currently defined output files (only
# the first is managed here, the rest in Makefile_data.
#
# scratch/rawgtfs/$location/$date/$zone/gtfs.zip
# scratch/proc/$location/$date/$zone-gtfs/
# scratch/proc/$location/$date/$zone.sqlite
# scratch/proc/$location/$date/$zone.stats
#os.chdir("../")


# To handle downloading once per week, we map all days to a "week
# number".  A download is done only once per week, as seen by the week
# numbers.  Week numbering starts at midnight Wednesday (UTC) and
# lasts one week.
WEEK_NUMBER_EPOCH = 1445990400     # Unixtime of 2015,10,28 00:00 UTC.
WEEK_NUMBER_INTERVAL = 3600*24*7   # One week in seconds
def week_number(dt):
    """Return normalized week number. Weeks since 2015-10-28 00:00 UTC (W).

    This is the hashing function used to download data once per week.
    Weeks start on Wednesdays.  Dates are hashed using this, and we
    download once per bucket.
    """
    ut = calendar.timegm(dt.timetuple())
    # seconds since 2015,10,28 00:00 UTC.
    ut -= WEEK_NUMBER_EPOCH
    weekn = ut // WEEK_NUMBER_INTERVAL
    return int(weekn)

def week_date(week_number):
    """Inverse of week_number: given week number, return datetime of start.

    Returns: datetime.datetime in UTC.  """
    ut = WEEK_NUMBER_EPOCH + (WEEK_NUMBER_INTERVAL * week_number)
    return datetime.datetime.utcfromtimestamp(ut)

def week_number_now():
    """The current week number"""
    dt = datetime.datetime.utcnow()
    week_now = week_number(dt)
    return week_now

class Location(object):
    """Location Manager - handles dealing with multiple locations.
    """
    slug = None
    name = None
    #gtfs_urls = { }
    def __init__(self, slug, data):
        """Set basic properties of the data structure"""
        self.slug = slug
        if data is None:
            self.data = { }
        elif isinstance(data, str):
            self.data = dict(notes=data)
        else:
            self.data = data
        self._parse_data(self.data)

    def _parse_data(self, data):
        """Initial parsing of scraping data.

        The data includes the different regions and URLs.  It sets up
        self.gtfs_urls[zone_name] to be the data for each zone, and if
        there is only one zone without a name, it is named "main".
        """
        self.name = data.get('name', self.slug)
        gtfs = data.get('gtfs')
        if isinstance(gtfs, str):
            self.gtfs_urls = dict(main=data['gtfs'])
        elif isinstance(gtfs, dict):
            self.gtfs_urls = gtfs
        elif gtfs is None:
            self.gtfs_urls = { }
        else:
            raise ValueError("Unknown gtfs key format: %s"%(gtfs, ))

    # A bunch of methods that return standard file paths.

    # Directories related to raw GTFS.
    @property
    def rawdir(self):
        """Base dir for GTFS downloads"""
        return join(RAW_DATA_DIR_PARENT_DIR, 'rawgtfs/%s/' % self.slug)

    def rawdir_dt(self, dt):
        """Base directory for one date"""
        return join(self.rawdir, dt.strftime('%Y-%m-%d'))

    def rawdir_zone(self, dt, zone):
        """Base directory for one GTFS file"""
        return join(self.rawdir, dt.strftime('%Y-%m-%d'), zone)

    @property
    def procdir(self):
        return join(RAW_DATA_DIR_PARENT_DIR, 'proc/%s/' % self.slug)

    def procdir_dt(self, dt):
        """Base directory for one date"""
        return join(self.procdir, dt.strftime('%Y-%m-%d'))

    def procdir_zone(self, dt, zone):
        """Base directory for one GTFS file"""
        return join(self.procdir, dt.strftime('%Y-%m-%d'), zone)

    def path_gtfsdir(self, dt, zone):
        """Directory for extracted GTFS files"""
        return join(self.procdir_zone(dt, zone), 'gtfs')

    def path_gtfszip(self, dt, zone):
        return join(self.rawdir_zone(dt, zone), 'gtfs.zip')

    # Functions Related to downloading and unpacking.
    def daily_download(self):
        """Download all files, if not already there.

        For each zone, see if there is already a download for this
        week (as found by week_number), and if not, then do that
        download.
        """
        for zone, url in self.gtfs_urls.items():
            week_now = week_number_now()
            # Get most recent download
            zone_dates = self.list_zone_dates()
            if zone not in zone_dates:
                week_lastdownload = float('-inf')
            else:
                week_lastdownload = week_number(zone_dates[zone][-1])
            if week_now > week_lastdownload:
                dt = datetime.datetime.utcnow()
                #zipfile = self.path_gtfszip(dt, zone)
                #if not os.path.exists(zip):
                self.gtfs_download(url, dt, zone)
                #self.gtfs_extract(dt, zone)

    def gtfs_download(self, url, dt, zone):
        """Do downloading of one file."""
        print("Downloading", self.slug, url, zone, dt)
        # Use only standard library functions to avoid dependencies.
        #furl = urllib.urlopen(url)
        opener = FancyURLopener()
        # We have to set up an authentication method on the opener if
        # we will need to authenticate.  This does HTTP BASIC only so
        # far.
        if 'authentication' in self.data:
            auth_name = self.data['authentication']
            auth = auth_data['sites'][auth_name]
            # A callback method which performs the authentication.
            # Return (user, pass) tuple.
            opener.prompt_user_passwd = \
                lambda host, realm: (auth['username'], auth['password'])
            # URL parameters auth method
            if 'url_suffix' in auth:
                url = url + auth['url_suffix']
        if "{API_KEY}" in url:
            try:
                auth_name = self.data['authentication']
            except KeyError:
                auth_name = self.name
            auth = auth_data['sites'][auth_name]
            url = url.format(API_KEY=auth['API_KEY'])
        # Make GTFS path.
        gtfs_path = self.path_gtfszip(dt, zone)
        util.makedirs(os.path.dirname(gtfs_path))
        # Open the URL.
        print("**** Connecting to %s" % url)
        # Open GTFS and relay data from web to file.
        with util.create_file(gtfs_path) as tmp_gtfs_path:
            opener.retrieve(url, tmp_gtfs_path)
        self.test_corrupted_zip(gtfs_path)
        # Done
    #def gtfs_extract(self, dt, zone):
    #    # Get paths, make target directory.
    #    gtfs_zip = self.path_gtfszip(dt, zone)
    #    gtfs_dir = self.path_gtfsdir(dt, zone)
    #    util.makedirs(gtfs_dir)
    #    # Open zipfile, get file names.
    #    zip = zipfile.ZipFile(gtfs_zip, 'r')
    #    names = zip.namelist()
    #    # Exatract every name that matches a basic sanity check.
    #    # zipfile module is supposed to do this too, but we'll be safe
    #    # here.
    #    for name in names:
    #        assert '/' not in name
    #        assert '\\' not in name
    #        assert not name.startswith('.')
    #        zip.extract(name, gtfs_dir)
    #    zip.close()

    def test_corrupted_zip(self, zip_path):
        import zipfile
        try:
            zip_to_test = zipfile.ZipFile(zip_path)
            warning = zip_to_test.testzip()
            if warning is not None:
                print("ERROR: zipfile created warning: " + str(warning))
            else:
                print("No warnings")
        except:
            print("ERROR: zipfile for " + self.name + " not created")

    # Getting information about available files
    def list_dates(self):
        """List all dates for which any files may have been downloaded."""
        if not os.path.isdir(self.rawdir):
            return [ ]
        names = os.listdir(self.rawdir)
        dates = [ ]
        for name in sorted(names):
            if os.path.isdir(join(self.rawdir, name)):
                dates.append(datetime.datetime.strptime(name, '%Y-%m-%d'))
        return sorted(dates)

    def list_files(self, dt):
        """List all zones downloaded on a given date."""
        path = self.rawdir_dt(dt)
        files = sorted(os.listdir(path))
        return files

    def list_zone_dates(self):
        """Return a dict of zone->[dt1, dt2, ...]"""
        data = { }
        for dt in self.list_dates():
            for zone in self.list_files(dt):
                data.setdefault(zone, []).append(dt)
        return data


def load_data(fname):
    """Load all YAML data and create objects"""
    data = yaml.load(open(fname))
    #print data
    sites = data['sites']
    locations = { }
    for name, data in sites.items():
        #if name not in ('test', 'test2'): continue
        locations[name] = Location(name, data)
    return locations


def main_status(locations):
    """Print a status report for downloads."""
    for name, L in sorted(locations.items()):
        dates = L.list_dates()
        if len(dates) == 0:
            print("No data for location: '" + name + "'")
        else:
            print(name + ":")
            for dt in L.list_dates():
                print("   ", dt.strftime("%Y-%m-%d"))
                for dir_ in sorted(L.list_files(dt)):
                    print("       ", dir_)

if __name__ == "__main__":
    # Credentials for sites that need it.
    auth_data = yaml.load(open('credentials.yaml'))
    cmd = sys.argv[1]
    # Second argument is used if one wants to download a specific city or cities (list)

    try:
        cities = sys.argv[2]
    except:
        cities = None
    locations = load_data('gtfs-sources.yaml')
    if cmd == 'status':
        main_status(locations)
    elif cmd == 'test':
        locations['test'].daily_download()
        locations['test2'].daily_download()

    elif cmd == 'scrape':
        if not os.path.exists(join(RAW_DATA_DIR_PARENT_DIR, 'rawgtfs/')):
            raise OSError(join(RAW_DATA_DIR_PARENT_DIR, 'rawgtfs/') + " is not available. Perhaps you should mount it?")
        print(time.strftime("%Y-%m-%d %H:%M%S"))

        for name, L in locations.items():

            try:
                if cities:
                    if name in cities:
                        L.daily_download()
                        print(name)
                else:
                    L.daily_download()
                    print(name)
            except Exception as e:
                import traceback
                print("import of " + name + " failed")
                print('=' * 20)
                traceback.print_exc()
                print('=' * 20)
        print("... done with all.")
