from sqlalchemy import Engine, func, desc, create_engine, inspect
from typing import List, Any
from sqlalchemy.exc import OperationalError
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timedelta
import time
from sqlalchemy.orm import sessionmaker
from config import DB_CONFIG, ALERT_THRESHOLDS
from db.data_processing import (
    get_dominant_conditions,
    get_temperature_stats,
    process_daily_weather_data,
)
from utils.temperature_utils import convert_temperature
from db.models import Base, WeatherData, DailySummary, UserConfig
import pandas as pd


def get_engine() -> Engine:
    """
    Gets an engine to the database, with a retry mechanism.
    """
    db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    retries = 5
    for i in range(retries):
        try:
            engine = create_engine(db_url)
            # Try connecting to the database
            connection = engine.connect()
            connection.close()
            return engine
        except OperationalError:
            print(f"Database connection failed ({i+1}/{retries}). Retrying in 5 seconds...")
            time.sleep(5)
    raise Exception("Could not connect to the database after several attempts")



def get_session():
    """
    Gets a session to the database.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def initialise_tables():
    """
    Initialise all the tables according to the schema defined above.
    """
    engine = get_engine()
    session = get_session()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "weather_data" not in tables:
        # Create only the missing table
        WeatherData.__table__.create(engine)
        print("Created weather data table")
    if "daily_summary" not in tables:
        DailySummary.__table__.create(engine)
        print("Created daily summary table")
    if "user_config" not in tables:
        UserConfig.__table__.create(engine)
        print("Created user config table")
        default_config = UserConfig(
            city=ALERT_THRESHOLDS["city"],
            threshold=ALERT_THRESHOLDS["threshold"],
            unit=ALERT_THRESHOLDS["unit"],
            consecutive_updates=ALERT_THRESHOLDS["consecutive_updates"],
        )
        session = get_session()
        try:
            session.add(default_config)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Ran into exception while creating single entry {str(e)}")
            raise e


def delete_old_weather_data() -> None:
    """
    Deletes all entries from the WeatherData table that are older than two days.

    This function connects to the database, calculates the cutoff datetime (current time minus two days),
    deletes all WeatherData records with a 'dt' earlier than the cutoff, and commits the transaction.

    It handles exceptions to ensure that any errors during the deletion process do not affect
    the integrity of the database.
    """
    session = get_session()
    try:
        # get cutoff before two days.
        cutoff_datetime = datetime.now() - timedelta(days=2)

        print(f"Deleting WeatherData entries older than: {cutoff_datetime}")

        # Perform the deletion
        deleted_count = (
            session.query(WeatherData)
            .filter(WeatherData.dt < cutoff_datetime)
            .delete(synchronize_session=False)
        )

        # Commit the transaction to make changes permanent
        session.commit()

        print(f"Successfully deleted {deleted_count} old WeatherData entries.")

    except Exception as e:
        # Rollback the transaction in case of any error to maintain database integrity
        session.rollback()
        print(f"Error deleting old WeatherData entries: {e}")

    finally:
        # Close the session to free up resources
        session.close()


def calculate_daily_summary() -> None:
    """
    It calculates the daily summary, and updates the daily_summary table
    if any entries have changed.
    """
    session = get_session()
    try:
        today = datetime.now().date()
        # Fetch data for today
        results = (
            session.query(WeatherData).filter(func.date(WeatherData.dt) == today).all()
        )
        if not results:
            print("No data available for today's summary.")
            return

        processed_df = process_daily_weather_data(results)
        temp_stats = get_temperature_stats(processed_df)
        dominant_stats = get_dominant_conditions(processed_df)

        # Merge temperature stats with dominant condition
        daily_summary = pd.merge(
            temp_stats,
            dominant_stats[["city", "date", "dominant_condition"]],
            on=["city", "date"],
        )

        summary_dicts = daily_summary.to_dict(orient="records")
        if not summary_dicts:
            print("No summaries to upsert.")
            return

        # Create an insert statement with ON CONFLICT DO UPDATE
        stmt = insert(DailySummary).values(summary_dicts)
        update_cols = {
            c.name: c for c in stmt.excluded if c.name not in ["city", "date"]
        }

        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["city", "date"], set_=update_cols
        )

        session.execute(upsert_stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error calculating daily summary: {e}")
    finally:
        session.close()


def check_alerts_in_app() -> List[str]:
    """
    Checks for temperature alerts for a given city based on the last 'consecutive_updates' entries.
    It fetches data from the user_config database.

    :return: List of alert messages if conditions are met.
    """
    alerts = []
    session = get_session()

    user_config = read_user_config()
    if not user_config:  # if we get a none object here, we return
        return alerts
    try:
        # get the last "consecutive_updates" entries from the database.
        recent_entries = (
            session.query(WeatherData)
            .filter(WeatherData.city == user_config.city)
            .order_by(desc(WeatherData.dt))
            .limit(user_config.consecutive_updates)
            .all()
        )
        # Check if we have enough data to evaluate. No
        # data if this is the case.
        if len(recent_entries) < user_config.consecutive_updates:
            return alerts
        # convert into correct temperature before checking for alerts
        recent_temps = [
            convert_temperature(entry.temp, user_config.unit)
            for entry in recent_entries
        ]

        # Check if all recent temperatures exceed the threshold
        if all(temp > user_config.threshold for temp in recent_temps):
            current_temp = recent_temps[0]

            # Construct the alert message
            alert_message = (
                f"Alert for {user_config.city}: Temperature exceeded {user_config.threshold}°{user_config.unit} "
                f"for {user_config.consecutive_updates} consecutive updates. Current temperature: {current_temp:.2f}°{user_config.unit[0]}"
            )
            alerts.append(alert_message)
        return alerts
    except Exception as e:
        print(f"Error in check_alerts_in_app: {e}")
        return alerts
    finally:
        # Ensure that the session is closed to free up resources
        session.close()


def load_summary_data() -> pd.DataFrame:
    """
    Gets all of the summarized data in a dataframe
    """
    session = get_session()
    try:
        # Fetch daily summaries
        summary_results = session.query(DailySummary).all()
        summary_df = pd.DataFrame(
            [
                {
                    "city": r.city,
                    "date": r.date,
                    "avg_temp": r.avg_temp,
                    "max_temp": r.max_temp,
                    "min_temp": r.min_temp,
                    "dominant_condition": r.dominant_condition,
                }
                for r in summary_results
            ]
        )

        return summary_df
    finally:
        session.close()


def store_weather_data(weather_data_list: dict[str, Any]):
    """
    Inserts or updates weather data into the weather_data table.

    :param weather_data_list: List of dictionaries containing weather data.
    """
    session = get_session()
    try:
        stmt = insert(WeatherData).values(weather_data_list)

        # Define the columns to update in case of conflict
        update_columns = {
            "main": stmt.excluded.main,
            "temp": stmt.excluded.temp,
            "feels_like": stmt.excluded.feels_like,
        }

        # Create an insert statement with ON CONFLICT DO UPDATE
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["city", "dt"], set_=update_columns
        )

        session.execute(stmt)
        session.commit()
        print(f"Successfully upserted {len(weather_data_list)} weather data entries.")
    except Exception as e:
        # Rollback the transaction in case of error
        session.rollback()
        print(f"Error inserting weather data: {e}")
    finally:
        # Close the session to free resources
        session.close()


# This is used to update_user_config, from which the alert will read from
# and run events.
def update_user_config(
    city: str, threshold: float, unit: str, consecutive_updates: int
):
    """
    Deletes all existing entries in the user_config table and inserts a new entry.

    :param city: The city for which the configuration is set.
    :param threshold: The temperature threshold.
    :param unit: The unit of temperature (Celsius, Fahrenheit, etc.).
    :param consecutive_updates: The number of consecutive updates.
    :param session: The SQLAlchemy session to perform database operations.
    """
    session = get_session()
    try:
        session.query(UserConfig).delete()

        # Create new entry
        new_config = UserConfig(
            city=city,
            threshold=threshold,
            unit=unit,
            consecutive_updates=consecutive_updates,
        )

        session.add(new_config)
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"Error updating user config: {e}")


def read_user_config() -> UserConfig:
    """
    Reads and returns the only entry in the user_config table.

    :param session: The SQLAlchemy session to perform database operations.
    :return: The single UserConfig entry or None if no entries exist.
    """
    session = get_session()
    try:
        user_config = session.query(UserConfig).first()
        return user_config
    except Exception as e:
        print(f"Error reading user config: {e}")
        return None
    


def get_latest_weather_data_for_city(city: str) -> WeatherData:
    """
    Retrieves the latest weather data entry for a given city.

    :param city: The city for which to retrieve the latest weather data.
    :return: The latest WeatherData object or None if not found.
    """
    session = get_session()
    try:
        latest_data = (
            session.query(WeatherData)
            .filter(WeatherData.city == city)
            .order_by(desc(WeatherData.dt))
            .first()
        )
        return latest_data
    except Exception as e:
        print(f"Error fetching latest weather data: {e}")
        return None
    finally:
        session.close()

