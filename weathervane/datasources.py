from collections import namedtuple
from urllib2 import urlopen
from parser import KNMIParser, BuienradarParser

weather_data = namedtuple('weather_data', ['wind_direction', 'wind_speed', 'wind_speed_max', 'air_pressure'])


class DataSource(object):
    def __init__(self, *args, **kwargs):
        self.fallback = kwargs['fallback-station']

    def get_data(self, conn, station_id):
        raise NotImplementedError("Do not use this interface directly, but subclass it and add your own functionality")

    def fetch_weather_data(self, url):
        response = urlopen(url)
        data = response.read()
        return data


class TestSource(DataSource):
    def __init__(self, *args, **kwargs):
        super(TestSource, self).__init__(*args, **kwargs)
        self.counter = 0

    def get_data(self, conn, station_id):
        """
        Test mode is used to output a predicable sequence of bytes to
        the output pins.
        The program will send 3 bytes every second to the pins.
        - Byte 1: an increasing counter (modulo 255)
        - Byte 2: a decreasing counter (idem)
        - Byte 3: switches between 0x55 and 0xAA

        """
        self.counter += 1

        if self.counter > 255:
            self.counter = 0

        if self.counter % 2:
            test = 0x55
        else:
            test = 0xAA

        wd = weather_data(wind_direction=self.counter % 255,
                          wind_speed=(255 - self.counter) % 255,
                          wind_speed_max=test,
                          air_pressure=None)

        conn.send(wd)
        conn.close()


class BuienradarSource(DataSource):
    def __init__(self, *args, **kwargs):
        super(TestSource, self).__init__(*args, **kwargs)

    def get_data(self, conn, station_id):
        data = self.fetch_weather_data("http://xml.buienradar.nl")
        parser = BuienradarParser(data, fallback=self.fallback)

        wd = weather_data(wind_direction=parser.get_wind_direction(station_id),
                          wind_speed=parser.get_wind_speed(station_id),
                          wind_speed_max=parser.get_wind_maximum(station_id),
                          air_pressure=parser.get_air_pressure(station_id))

        conn.send(wd)
        conn.close()


class KNMISource(DataSource):
    def __init__(self, *args, **kwargs):
        super(TestSource, self).__init__(*args, **kwargs)

    def get_data(self, conn, station_id):
        """
        >>> from multiprocessing import Pipe
        >>> knmi = KNMISource()
        >>> p1, p2 = Pipe()
        >>> s = knmi.get_data(p2, 251)
        >>> data = p1.recv()
        >>> print data
        """
        data = self.fetch_weather_data("http://www.knmi.nl/actueel/")
        parser = KNMIParser(data)

        wd = weather_data(wind_direction=parser.get_wind_direction(station_id),
                          wind_speed=parser.get_wind_speed(station_id),
                          wind_speed_max=parser.get_wind_maximum(station_id),
                          air_pressure=parser.get_air_pressure(station_id))

        conn.send(wd)
        conn.close()


class RijkswaterstaatSource(object):
    def __init__(self):
        raise NotImplementedError("Rijkswaterstaat is not yet ready")
        # http://www.rijkswaterstaat.nl/apps/geoservices/rwsnl/awd.php?mode=html

if __name__ == '__main__':
    import doctest
    doctest.testmod()