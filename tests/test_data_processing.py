import unittest
import pandas as pd
from datetime import datetime
from db.data_processing import (
    process_daily_weather_data,
    get_temperature_stats,
    get_dominant_conditions,
)
from db.db_manager import WeatherData
from typing import List


# Test class
class TestWeatherDataProcessing(unittest.TestCase):
    def test_process_daily_weather_data(self):
        # Prepare mock WeatherData records
        weather_records = [
            WeatherData(
                city="Delhi",
                temp=30.0,
                main="Clear",
                dt=datetime(2023, 10, 19, 9, 0, 0),
            ),
            WeatherData(
                city="Delhi",
                temp=32.0,
                main="Clouds",
                dt=datetime(2023, 10, 19, 15, 0, 0),
            ),
            WeatherData(
                city="Mumbai",
                temp=28.0,
                main="Rain",
                dt=datetime(2023, 10, 19, 12, 0, 0),
            ),
            WeatherData(
                city="Mumbai",
                temp=29.0,
                main="Rain",
                dt=datetime(2023, 10, 19, 20, 0, 0),
            ),
        ]

        # Call the function
        df = process_daily_weather_data(weather_records)

        # Check the dataframe
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        # Check that the columns are correct
        expected_columns = ["city", "temp", "main", "dt", "date", "hour", "weight"]
        self.assertListEqual(list(df.columns), expected_columns)
        # Check the weights
        expected_weights = [2, 2, 2, 1]  # Based on the assign_weight function
        self.assertListEqual(df["weight"].tolist(), expected_weights)
        # Check date and hour
        expected_dates = [datetime(2023, 10, 19).date()] * 4
        self.assertListEqual(df["date"].tolist(), expected_dates)
        expected_hours = [9, 15, 12, 20]
        self.assertListEqual(df["hour"].tolist(), expected_hours)

    def test_get_temperature_stats(self):
        # Prepare a processed dataframe
        data = {
            "city": ["Delhi", "Delhi", "Mumbai", "Mumbai"],
            "temp": [30.0, 32.0, 28.0, 29.0],
            "main": ["Clear", "Clouds", "Rain", "Rain"],
            "dt": [
                datetime(2023, 10, 19, 9, 0, 0),
                datetime(2023, 10, 19, 15, 0, 0),
                datetime(2023, 10, 19, 12, 0, 0),
                datetime(2023, 10, 19, 20, 0, 0),
            ],
            "date": [datetime(2023, 10, 19).date()] * 4,
            "hour": [9, 15, 12, 20],
            "weight": [2, 2, 2, 1],
        }
        df = pd.DataFrame(data)

        # Call the function
        temp_stats = get_temperature_stats(df)

        # Expected result
        expected_data = {
            "city": ["Delhi", "Mumbai"],
            "date": [datetime(2023, 10, 19).date()] * 2,
            "avg_temp": [(30.0 + 32.0) / 2, (28.0 + 29.0) / 2],
            "max_temp": [32.0, 29.0],
            "min_temp": [30.0, 28.0],
        }
        expected_df = pd.DataFrame(expected_data)

        # Use pandas testing functions
        pd.testing.assert_frame_equal(temp_stats.reset_index(drop=True), expected_df)

    def test_get_dominant_conditions(self):
        # Prepare a processed dataframe
        data = {
            "city": ["Delhi", "Delhi", "Mumbai", "Mumbai", "Mumbai"],
            "temp": [30.0, 32.0, 28.0, 29.0, 27.0],
            "main": ["Clear", "Clouds", "Rain", "Rain", "Clouds"],
            "dt": [
                datetime(2023, 10, 19, 9, 0, 0),
                datetime(2023, 10, 19, 15, 0, 0),
                datetime(2023, 10, 19, 12, 0, 0),
                datetime(2023, 10, 19, 20, 0, 0),
                datetime(2023, 10, 19, 8, 0, 0),
            ],
            "date": [datetime(2023, 10, 19).date()] * 5,
            "hour": [9, 15, 12, 20, 8],
            "weight": [2, 2, 2, 1, 2],
        }
        df = pd.DataFrame(data)

        # Call the function
        dominant_conditions = get_dominant_conditions(df)

        # Expected result
        expected_data = {
            "city": ["Delhi", "Mumbai"],
            "date": [datetime(2023, 10, 19).date()] * 2,
            "dominant_condition": ["Clear", "Rain"],
        }
        expected_df = pd.DataFrame(expected_data)
        # We only need to compare the 'city', 'date', 'dominant_condition' columns
        expected_df = expected_df[["city", "date", "dominant_condition"]]
        dominant_conditions = dominant_conditions[
            ["city", "date", "dominant_condition"]
        ]

        # Use pandas testing functions
        pd.testing.assert_frame_equal(
            dominant_conditions.reset_index(drop=True), expected_df
        )


if __name__ == "__main__":
    unittest.main()
