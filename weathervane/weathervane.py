import argparse
import logging
import logging.handlers
from multiprocessing import Process, Pipe
from time import sleep
from weatherdata.datasources import BuienradarSource
from interfaces.testinterface import TestInterface
from interfaces.weathervaneinterface import WeatherVaneInterface


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
        logging.info("Starting testmode")
        interface = TestInterface(channel=0, frequency=25000)
        counter = 0

        while True:
            counter += 1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter % 255, (255 - counter) % 255, test]

            interface.send(data)
            sleep(1)

    def main(self, interval, station_id=6323):
        logging.info("Starting normal operation")
        interface = WeatherVaneInterface(channel=0, frequency=250000)
        logging.debug("Using " + str(interface))
        weather_data = {'wind_direction': None, 'wind_speed': None, 'wind_speed_max': None, 'air_pressure': None}
        data_source = BuienradarSource()
        pipe_end_1, pipe_end_2 = Pipe()
        counter = 0

        while True:
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TBD")
    parser.add_argument('-t', '--test', action='store_true', default=False, help="run the program in test mode")
    parser.add_argument('-i', '--interval', action='store', type=int, default=300,
                        help="specify the amount of seconds between each time the weather data is collected")
    wv = WeatherVane()

    args = parser.parse_args()

    weathervane_logger = logging.getLogger('')
    weathervane_logger.setLevel(logging.DEBUG)
    handler = logging.handlers.TimedRotatingFileHandler(filename="weathervane.log",
                                                        when="midnight",
                                                        interval=1,
                                                        backupCount=7)
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")
    handler.setFormatter(formatter)
    weathervane_logger.addHandler(handler)

    if args.test:
        wv.test_mode()
    else:
        wv.main(interval=args.interval)
