#!/usr/bin/env python

import argparse
import logging
import logging.handlers
from multiprocessing import Process, Pipe
from time import sleep
from gpio import TestInterface

from weathervaneinterface import WeatherVaneInterface


class WeatherVane(object):
    def test_mode(self):
        """
        Test mode is used to output a predicable sequence of bytes to
        the output pins.
        The program will send 3 bytes every second to the pins.
        - Byte 1: an increasing counter (modulo 255)
        - Byte 2: a decreasing counter (idem)
        - Byte 3: switches between 0x55 and 0xAA

        """
        logging.info("Starting test mode")
        interface = TestInterface(channel=0, frequency=25000)
        counter = 0

        while True:
            counter += 1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter % 255, (255-counter) % 255, test]

            interface.send(data)
            sleep(1)

    def get_source(self, source):
        if source == 'buienradar':
            from datasources import BuienradarSource
            return BuienradarSource()
        elif source == 'knmi':
            from datasources import KNMISource
            return KNMISource()
        elif source == 'rijkswaterstaat':
            from datasources import RijkswaterstaatSource
            return RijkswaterstaatSource()
        elif source == 'test':
            from datasources import TestSource
            return TestSource()
        else:
            raise NameError('Data provider not found')

    def main(self, interval, station_id, source='buienradar'):
        logging.info("Starting operation")
        interface = WeatherVaneInterface(channel=0, frequency=250000)

        logging.debug("Using " + str(interface))
        weather_data = {'wind_direction': None, 'wind_speed': None, 'wind_speed_max': None, 'air_pressure': None}

        data_source = self.get_source(source)

        pipe_end_1, pipe_end_2 = Pipe()
        counter = 0

        selected_station = interface.get_selected_station()

        while True:
            if (counter % 3) == 0:  # check the station selection every three seconds
                station_id = interface.get_selected_station()
                if station_id != selected_station:  # reset if a new station is selected
                    counter = 0
                    selected_station = station_id
                    logging.info("New station selected: {}".format(station_id))

            if (counter % interval) == 0:
                counter = 0
                p = Process(target=data_source.get_data, args=(pipe_end_1, station_id))
                p.start()

            if pipe_end_2.poll(0):
                weather_data = pipe_end_2.recv()
                logging.info("Received data:" + str(weather_data))

            interface.send(weather_data)

            counter += 1
            sleep(1)

    def set_logger(self):
        weathervane_logger = logging.getLogger('')
        weathervane_logger.setLevel(logging.DEBUG)
        handler = logging.handlers.TimedRotatingFileHandler(filename="weathervane.log",
                                                            when="midnight",
                                                            interval=1,
                                                            backupCount=7)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")
        handler.setFormatter(formatter)
        weathervane_logger.addHandler(handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather data from a provider and send it through SPI")
    parser.add_argument('-t', '--test', action='store_true', default=False, help="run the program in test mode")
    parser.add_argument('-i', '--interval', action='store', type=int, default=300,
                        help="specify the interval (in seconds) when the weather data is retrieved")
    parser.add_argument('-s', '--station', action='store', type=int, default=None,
                        help="the id of the the weather station from which the weather data is retrieved")
    parser.add_argument('-p', '--provider', choices=['buienradar', 'knmi', 'rijkswaterstaat'],
                        help='select the provider', default='buienradar')
    args = parser.parse_args()

    wv = WeatherVane()
    wv.set_logger()
    logging.info(args)

    if args.test:
        wv.test_mode()
    else:
        wv.main(interval=args.interval, source=args.provider, station_id=args.station)
