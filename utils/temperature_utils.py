from config import TEMP_UNIT_KELVIN, TEMP_UNIT_CELSIUS, TEMP_UNIT_FAHRENHEIT
import pandas as pd


def kelvin_to_celsius(kelvin: float) -> float:
    """
    converts a float value kelvin to a fahrenheit.
    :param kelvin: temperature in kelvin
    :return: temperature in celsius
    """
    return kelvin - 273.15


def kelvin_to_fahrenheit(kelvin: float) -> float:
    """
    converts a float value kelvin to a fahrenheit.
    :param kelvin: temperature in kelvin
    :return: temperature in fahrenheit
    """
    return (kelvin_to_celsius(kelvin)) * 9 / 5 + 32


def convert_temperature(kelvin: float, to_unit: str) -> float:
    """
    This converts a single float into celsius/fahrenheit depending
    on your needs.
    :param kelvin: temperature in kelvin
    :return: the dataframe column with converted temperatures.
    """
    if to_unit == TEMP_UNIT_CELSIUS:
        return kelvin_to_celsius(kelvin)
    elif to_unit == TEMP_UNIT_FAHRENHEIT:
        return kelvin_to_fahrenheit(kelvin)
    elif to_unit == TEMP_UNIT_KELVIN:
        return kelvin
    else:
        return kelvin


def convert_temperature_series(temp_series: pd.DataFrame, to_unit: str) -> pd.DataFrame:
    """
    This converts a pandas dataframe row into celsius/fahrenheit depending
    on your needs.
    :param temp_series: pandas DataFrame with one column, with temperature
    :return: the dataframe column with converted temperatures.
    """
    if len(temp_series.shape) == 2 and temp_series.shape[1] != 1:
        print("invalid dataframe passed in")
        return temp_series
    if to_unit == TEMP_UNIT_CELSIUS:
        return temp_series.apply(kelvin_to_celsius)
    elif to_unit == TEMP_UNIT_FAHRENHEIT:
        return temp_series.apply(kelvin_to_fahrenheit)
    elif to_unit == TEMP_UNIT_KELVIN:
        return temp_series
    else:
        return temp_series


def assign_weight(hour):
    """
    Assigns weight to a weather condition based on the hour of the day.
    Hours between 9 AM (inclusive) and 5 PM (exclusive) are given a higher
    weight.

    :param hour: Integer representing the hour of the day (0-23)
    :return: Integer weight
    """
    if 9 <= hour < 17:
        return 2  # Higher weight for daytime conditions
    return 1  # Lower weight for nighttime conditions
