import unittest
from unittest.mock import patch
from config import ALERT_THRESHOLDS
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd
from db.db_manager import (
    WeatherData,
    DailySummary,
    UserConfig,
    initialise_tables,
    delete_old_weather_data,
    update_user_config,
    calculate_daily_summary,
    check_alerts_in_app,
    load_summary_data,
    store_weather_data,
)
from db.data_processing import (
    process_daily_weather_data,
    get_temperature_stats,
    get_dominant_conditions,
)


# Mock dependencies if necessary
def assign_weight(hour):
    """
    Mock assign_weight function for testing purposes.
    Let's define weight as:
    - Hours 6 to 18 (6 AM to 6 PM): weight 2
    - Otherwise: weight 1
    """
    if 6 <= hour <= 18:
        return 2
    else:
        return 1


class TestDBManager(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine)

        # Create tables
        WeatherData.metadata.create_all(self.engine)
        DailySummary.metadata.create_all(self.engine)

        # Patch get_engine and get_session to use the in-memory database
        self.get_engine_patcher = patch(
            "db.db_manager.get_engine", return_value=self.engine
        )
        self.mock_get_engine = self.get_engine_patcher.start()
        self.get_session_patcher = patch("db.db_manager.get_session", self.get_session)
        self.mock_get_session = self.get_session_patcher.start()

    def tearDown(self):
        self.get_engine_patcher.stop()
        self.get_session_patcher.stop()
        self.engine.dispose()

    def get_session(self):
        return self.Session()

    def test_initialise_tables(self):
        session = self.get_session()
        # Drop existing tables
        WeatherData.__table__.drop(bind=self.engine)
        DailySummary.__table__.drop(bind=self.engine)
        UserConfig.__table__.drop(bind=self.engine)

        # Run initialise_tables
        initialise_tables()
        # Check if tables exist
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        self.assertIn("weather_data", tables)
        self.assertIn("daily_summary", tables)
        self.assertIn("user_config", tables)

        # Check that default user config has been inserted
        user_config = session.query(UserConfig).first()
        self.assertIsNotNone(user_config)
        self.assertEqual(user_config.city, ALERT_THRESHOLDS["city"])
        self.assertEqual(user_config.threshold, ALERT_THRESHOLDS["threshold"])
        self.assertEqual(user_config.unit, ALERT_THRESHOLDS["unit"])
        self.assertEqual(
            user_config.consecutive_updates, ALERT_THRESHOLDS["consecutive_updates"]
        )
        session.close()

    def test_store_weather_data(self):
        weather_data_list = [
            {
                "city": "Delhi",
                "main": "Clear",
                "temp": 30.0,
                "feels_like": 32.0,
                "dt": datetime.now(),
            },
            {
                "city": "Mumbai",
                "main": "Rain",
                "temp": 28.0,
                "feels_like": 30.0,
                "dt": datetime.now(),
            },
        ]
        store_weather_data(weather_data_list)
        session = self.Session()
        results = session.query(WeatherData).all()
        self.assertEqual(len(results), 2)
        for data in weather_data_list:
            record = session.query(WeatherData).filter_by(city=data["city"]).first()
            self.assertIsNotNone(record)
            self.assertEqual(record.main, data["main"])
            self.assertEqual(record.temp, data["temp"])
            self.assertEqual(record.feels_like, data["feels_like"])
            self.assertEqual(record.dt.date(), data["dt"].date())
            self.assertEqual(record.dt.hour, data["dt"].hour)
        session.close()

    def test_delete_old_weather_data(self):
        session = self.Session()
        now = datetime.now()
        old_date = now - timedelta(days=3)
        new_date = now - timedelta(days=1)
        weather_data_list = [
            WeatherData(
                city="Delhi",
                main="Clear",
                temp=30.0,
                feels_like=32.0,
                dt=old_date,
            ),
            WeatherData(
                city="Mumbai",
                main="Rain",
                temp=28.0,
                feels_like=30.0,
                dt=new_date,
            ),
        ]
        session.add_all(weather_data_list)
        session.commit()
        delete_old_weather_data()
        remaining_data = session.query(WeatherData).all()
        self.assertEqual(len(remaining_data), 1)
        self.assertEqual(remaining_data[0].city, "Mumbai")
        session.close()

    def test_calculate_daily_summary(self):
        session = self.Session()
        now = datetime.now()
        weather_data_list = [
            WeatherData(
                city="Delhi",
                main="Clear",
                temp=30.0,
                feels_like=32.0,
                dt=now.replace(hour=9),
            ),
            WeatherData(
                city="Delhi",
                main="Clouds",
                temp=32.0,
                feels_like=34.0,
                dt=now.replace(hour=15),
            ),
            WeatherData(
                city="Mumbai",
                main="Rain",
                temp=28.0,
                feels_like=30.0,
                dt=now.replace(hour=12),
            ),
            WeatherData(
                city="Mumbai",
                main="Rain",
                temp=29.0,
                feels_like=31.0,
                dt=now.replace(hour=20),
            ),
        ]
        session.add_all(weather_data_list)
        session.commit()
        calculate_daily_summary()
        summaries = session.query(DailySummary).all()
        self.assertEqual(len(summaries), 2)
        for summary in summaries:
            if summary.city == "Delhi":
                self.assertEqual(summary.avg_temp, 31.0)
                self.assertEqual(summary.max_temp, 32.0)
                self.assertEqual(summary.min_temp, 30.0)
                self.assertIn(summary.dominant_condition, ["Clear", "Clouds"])
            elif summary.city == "Mumbai":
                self.assertEqual(summary.avg_temp, 28.5)
                self.assertEqual(summary.max_temp, 29.0)
                self.assertEqual(summary.min_temp, 28.0)
                self.assertEqual(summary.dominant_condition, "Rain")
        session.close()

    def test_check_alerts_in_app(self):
        session = self.Session()
        now = datetime.now()
        weather_data_list = [
            WeatherData(
                city="Delhi",
                main="Clear",
                temp=308.15,
                feels_like=310.15,
                dt=now - timedelta(hours=2),
            ),
            WeatherData(
                city="Delhi",
                main="Clouds",
                temp=309.15,  # 36.0 + 273.15
                feels_like=311.15,  # 38.0 + 273.15
                dt=now - timedelta(hours=1),
            ),
            WeatherData(
                city="Delhi",
                main="Clear",
                temp=310.15,  # 37.0 + 273.15
                feels_like=312.15,  # 39.0 + 273.15
                dt=now,
            ),
            WeatherData(
                city="Mumbai",
                main="Rain",
                temp=301.15,  # 28.0 + 273.15
                feels_like=303.15,  # 30.0 + 273.15
                dt=now - timedelta(hours=1),
            ),
            WeatherData(
                city="Mumbai",
                main="Rain",
                temp=302.15,  # 29.0 + 273.15
                feels_like=304.15,  # 31.0 + 273.15
                dt=now,
            ),
        ]
        session.add_all(weather_data_list)
        session.commit()
        update_user_config(
            city="Delhi", threshold=34.0, unit="Celsius", consecutive_updates=3
        )
        alerts_delhi = check_alerts_in_app()
        self.assertEqual(len(alerts_delhi), 1)
        self.assertIn("Alert for Delhi", alerts_delhi[0])
        update_user_config(
            city="Mumbai", threshold=34.0, unit="Celsius", consecutive_updates=3
        )
        alerts_mumbai = check_alerts_in_app()
        self.assertEqual(len(alerts_mumbai), 0)
        session.close()

    def test_load_summary_data(self):
        session = self.Session()
        today = datetime.now().date()
        summary_data = [
            DailySummary(
                city="Delhi",
                date=today,
                avg_temp=31.0,
                max_temp=32.0,
                min_temp=30.0,
                dominant_condition="Clear",
            ),
            DailySummary(
                city="Mumbai",
                date=today,
                avg_temp=28.5,
                max_temp=29.0,
                min_temp=28.0,
                dominant_condition="Rain",
            ),
        ]
        session.add_all(summary_data)
        session.commit()
        df = load_summary_data()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 2)
        self.assertListEqual(sorted(df["city"].tolist()), ["Delhi", "Mumbai"])
        delhi_summary = df[df["city"] == "Delhi"].iloc[0]
        self.assertEqual(delhi_summary["avg_temp"], 31.0)
        self.assertEqual(delhi_summary["max_temp"], 32.0)
        self.assertEqual(delhi_summary["min_temp"], 30.0)
        self.assertEqual(delhi_summary["dominant_condition"], "Clear")
        session.close()

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
        expected_columns = ["city", "temp", "main", "dt", "date", "hour", "weight"]
        self.assertListEqual(list(df.columns), expected_columns)
        expected_weights = [2, 2, 2, 1]
        self.assertListEqual(df["weight"].tolist(), expected_weights)
        expected_dates = [datetime(2023, 10, 19).date()] * 4
        self.assertListEqual(df["date"].tolist(), expected_dates)
        expected_hours = [9, 15, 12, 20]
        self.assertListEqual(df["hour"].tolist(), expected_hours)

    def test_get_temperature_stats(self):
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
        temp_stats = get_temperature_stats(df)
        expected_data = {
            "city": ["Delhi", "Mumbai"],
            "date": [datetime(2023, 10, 19).date()] * 2,
            "avg_temp": [31.0, 28.5],
            "max_temp": [32.0, 29.0],
            "min_temp": [30.0, 28.0],
        }
        expected_df = pd.DataFrame(expected_data)
        pd.testing.assert_frame_equal(temp_stats.reset_index(drop=True), expected_df)

    def test_get_dominant_conditions(self):
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
        dominant_conditions = get_dominant_conditions(df)
        expected_data = {
            "city": ["Delhi", "Mumbai"],
            "date": [datetime(2023, 10, 19).date()] * 2,
            "dominant_condition": ["Clear", "Rain"],
        }
        expected_df = pd.DataFrame(expected_data)
        expected_df = expected_df[["city", "date", "dominant_condition"]]
        dominant_conditions = dominant_conditions[
            ["city", "date", "dominant_condition"]
        ]
        pd.testing.assert_frame_equal(
            dominant_conditions.reset_index(drop=True), expected_df
        )


if __name__ == "__main__":
    unittest.main()
