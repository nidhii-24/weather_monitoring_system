import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
from utils.temperature_utils import (
    kelvin_to_celsius,
    kelvin_to_fahrenheit,
    convert_temperature_series,
    assign_weight,
    convert_temperature,
)
from config import TEMP_UNIT_CELSIUS, TEMP_UNIT_FAHRENHEIT, TEMP_UNIT_KELVIN


class TestConvertTemperature(unittest.TestCase):
    """Unit tests for the convert_temperature function."""

    def test_convert_to_celsius(self):
        """Test conversion from Kelvin to Celsius."""
        kelvin = 300.0
        expected_celsius = 26.85  # 300 - 273.15
        result = convert_temperature(kelvin, TEMP_UNIT_CELSIUS)
        self.assertAlmostEqual(result, expected_celsius, places=2)

    def test_convert_to_fahrenheit(self):
        """Test conversion from Kelvin to Fahrenheit."""
        kelvin = 300.0
        expected_fahrenheit = 80.33  # (300 - 273.15) * 9/5 + 32
        result = convert_temperature(kelvin, TEMP_UNIT_FAHRENHEIT)
        self.assertAlmostEqual(result, expected_fahrenheit, places=2)

    def test_convert_to_kelvin(self):
        """Test conversion from Kelvin to Kelvin (no conversion)."""
        kelvin = 300.0
        expected_kelvin = 300.0
        result = convert_temperature(kelvin, TEMP_UNIT_KELVIN)
        self.assertEqual(result, expected_kelvin)

    def test_convert_to_unsupported_unit(self):
        """Test conversion with an unsupported unit."""
        kelvin = 300.0
        unsupported_unit = "Rankine"
        expected = kelvin  # Should return the original Kelvin value
        result = convert_temperature(kelvin, unsupported_unit)
        self.assertEqual(result, expected)

    def test_negative_kelvin_to_celsius(self):
        """Test conversion of negative Kelvin to Celsius."""
        kelvin = -10.0
        expected_celsius = -283.15  # -10 - 273.15
        result = convert_temperature(kelvin, TEMP_UNIT_CELSIUS)
        self.assertAlmostEqual(result, expected_celsius, places=2)

    def test_zero_kelvin_to_fahrenheit(self):
        """Test conversion of 0 Kelvin to Fahrenheit."""
        kelvin = 0.0
        expected_fahrenheit = -459.67  # Absolute zero in Fahrenheit
        result = convert_temperature(kelvin, TEMP_UNIT_FAHRENHEIT)
        self.assertAlmostEqual(result, expected_fahrenheit, places=2)


class TestTemperatureUtils(unittest.TestCase):
    def test_kelvin_to_celsius(self):
        self.assertAlmostEqual(kelvin_to_celsius(0), -273.15, places=2)
        self.assertAlmostEqual(kelvin_to_celsius(273.15), 0.0, places=2)
        self.assertAlmostEqual(kelvin_to_celsius(300), 26.85, places=2)

    def test_kelvin_to_fahrenheit(self):
        self.assertAlmostEqual(kelvin_to_fahrenheit(0), -459.67, places=2)
        self.assertAlmostEqual(kelvin_to_fahrenheit(273.15), 32.0, places=2)
        self.assertAlmostEqual(kelvin_to_fahrenheit(300), 80.33, places=2)

    def test_convert_temperature_series_celsius(self):
        df = pd.DataFrame({"temp": [300.0, 310.0]})
        converted = convert_temperature_series(df[["temp"]], "Celsius")
        expected = pd.DataFrame({"temp": [26.85, 36.85]})
        assert_frame_equal(converted.reset_index(drop=True), expected)

    def test_convert_temperature_series_fahrenheit(self):
        df = pd.DataFrame({"temp": [300.0, 310.0]})
        converted = convert_temperature_series(df[["temp"]], "Fahrenheit")
        expected = pd.DataFrame({"temp": [80.33, 98.33]})
        assert_frame_equal(converted.reset_index(drop=True), expected)

    def test_convert_temperature_series_kelvin(self):
        df = pd.DataFrame({"temp": [300.0, 310.0]})
        converted = convert_temperature_series(df[["temp"]], "Kelvin")
        expected = pd.DataFrame({"temp": [300.0, 310.0]})
        assert_frame_equal(converted.reset_index(drop=True), expected)

    def test_convert_temperature_series_invalid_unit(self):
        df = pd.DataFrame({"temp": [300.0, 310.0]})
        converted = convert_temperature_series(df[["temp"]], "InvalidUnit")
        expected = df[["temp"]]
        assert_frame_equal(converted.reset_index(drop=True), expected)

    def test_convert_temperature_series_invalid_dataframe(self):
        df = pd.DataFrame({"temp1": [300.0], "temp2": [310.0]})
        converted = convert_temperature_series(df, "Celsius")
        expected = df
        assert_frame_equal(converted.reset_index(drop=True), expected)

    def test_assign_weight_daytime(self):
        for hour in range(9, 17):
            weight = assign_weight(hour)
            self.assertEqual(weight, 2)

    def test_assign_weight_nighttime(self):
        for hour in list(range(0, 9)) + list(range(17, 24)):
            weight = assign_weight(hour)
            self.assertEqual(weight, 1)


if __name__ == "__main__":
    unittest.main()
