import logging
import requests

from weathervane.parser import BuienradarParser

DEFAULT_WEATHER_DATA = {
    'error': True,
    'air_pressure': 900,
    'humidity': 0,
    'rain': True,
    'random': 0,
    'temperature': -39.9,
    'temperature_10_cm': -39.9,
    'apparent_temperature': 0,
    'wind_direction': 'N',
    'wind_direction_code': 'N',
    'wind_direction_degrees': 0,
    'wind_speed': 0,
    'wind_speed_max': 0,
    'wind_speed_bft': 0
}


def fetch_weather_data(conn, *args, **kwargs):
    wd = None

    try:
        r = requests.get("https://api.buienradar.nl/data/public/1.1/jsonfeed", timeout=10)
        if r.status_code == 200:
            logging.info('Weather data retrieved in {} ms'.format(r.elapsed))
            bp = BuienradarParser(*args, **kwargs)
            wd = bp.parse(r.text)
    except (ConnectionError, TimeoutError):
        logging.warning('Retrieving data failed. Setting error.')
        wd = DEFAULT_WEATHER_DATA

    conn.send(wd)
    conn.close()
