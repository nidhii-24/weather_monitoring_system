from typing import List

from sqlalchemy import func
import pandas as pd
from db.models import WeatherData
from utils.temperature_utils import assign_weight


def process_daily_weather_data(weather_records: List[WeatherData]) -> pd.DataFrame:
    """
    Converts weather records into a pandas DataFrame and adds a weight column based on the time of day.

    :param weather_records: List of WeatherData records
    :return: pandas DataFrame with weather data and weights
    """
    df = pd.DataFrame(
        [
            {
                "city": record.city,
                "temp": record.temp,
                "main": record.main,
                "dt": record.dt,
            }
            for record in weather_records
        ]
    )

    df["date"] = df["dt"].dt.date
    df["hour"] = df["dt"].dt.hour
    df["weight"] = df["hour"].apply(assign_weight)

    return df


def get_temperature_stats(processed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the temperature stats of each city, by date.

    :param df: pandas DataFrame with weather data and weights
    :return: pandas DataFrame with aggregated daily summaries
    """
    temp_stats = (
        processed_df.groupby(["city", "date"])
        .agg(
            avg_temp=("temp", "mean"),
            max_temp=("temp", "max"),
            min_temp=("temp", "min"),
        )
        .reset_index()
    )
    return temp_stats


def get_dominant_conditions(processed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the most dominant condition by giving it weights.
    Any time between 9am to 5pm of the day is given extra weight
    as more humans would only care about what happens in the day.

    It filters out entries from the weather_data table by date and
    Finds out the main which has maximum weight and returns that as a
    dataframe.
    """

    # Calculate weighted dominant condition. This will group by city, date
    # and the weather condition - and sum all the weights across.
    dominant_conditions = (
        processed_df.groupby(["city", "date", "main"])["weight"].sum().reset_index()
    )

    # For each city and date, select the condition with the highest weighted count
    # We sort weight by descending as we want the largest weight first.
    dominant_conditions = dominant_conditions.sort_values(
        ["city", "date", "weight"], ascending=[True, True, False]
    )
    # Choose the main with the maximum weight
    dominant_condition = (
        dominant_conditions.groupby(["city", "date"]).first().reset_index()
    )
    dominant_condition = dominant_condition.rename(
        columns={"main": "dominant_condition"}
    )

    return dominant_condition
