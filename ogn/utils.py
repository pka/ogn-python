import requests
import csv
from io import StringIO

from .model import Device, AddressOrigin

from geopy.geocoders import Nominatim

DDB_URL = "http://ddb.glidernet.org/download"


address_prefixes = {'F': 'FLR',
                    'O': 'OGN',
                    'I': 'ICA'}


def get_ddb(csvfile=None):
    if csvfile is None:
        r = requests.get(DDB_URL)
        rows = '\n'.join(i for i in r.text.splitlines() if i[0] != '#')
        address_origin = AddressOrigin.ogn_ddb
    else:
        r = open(csvfile, 'r')
        rows = ''.join(i for i in r.readlines() if i[0] != '#')
        address_origin = AddressOrigin.user_defined

    data = csv.reader(StringIO(rows), quotechar="'", quoting=csv.QUOTE_ALL)

    devices = list()
    for row in data:
        flarm = Device()
        flarm.address_type = row[0]
        flarm.address = row[1]
        flarm.aircraft = row[2]
        flarm.registration = row[3]
        flarm.competition = row[4]
        flarm.tracked = row[5] == 'Y'
        flarm.identified = row[6] == 'Y'

        flarm.address_origin = address_origin

        devices.append(flarm)

    return devices


def get_trackable(ddb):
    l = []
    for i in ddb:
        if i.tracked and i.address_type in address_prefixes:
            l.append('{}{}'.format(address_prefixes[i.address_type], i.address))
    return l


def get_country_code(latitude, longitude):
    geolocator = Nominatim()
    location = geolocator.reverse("%f, %f" % (latitude, longitude))
    try:
        country_code = location.raw["address"]["country_code"]
    except KeyError:
        country_code = None
    return country_code
