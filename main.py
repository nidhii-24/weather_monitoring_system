import schedule
import time
from weather.weather_data import get_all_cities_weather
from db.db_manager import (
    initialise_tables,
    delete_old_weather_data,
    store_weather_data,
    calculate_daily_summary,
    check_alerts_in_app,
)
from config import RETRIEVAL_INTERVAL, CLEANUP_INTERVAL

def get_latest_weather_info():
    print("Starting weather data retrieval and processing job...")
    weather_data_list = get_all_cities_weather()
    if weather_data_list:
        store_weather_data(weather_data_list)
        calculate_daily_summary()
    else:
        print("No weather data retrieved.")
    check_alerts_in_app()
    print("Job completed.\n")

def setup_schedules_and_db():
    initialise_tables()
    schedule.every(RETRIEVAL_INTERVAL).minutes.do(get_latest_weather_info)
    schedule.every(CLEANUP_INTERVAL).hours.do(delete_old_weather_data)
    print(
        f"Weather Monitoring System started. Data will be retrieved every {RETRIEVAL_INTERVAL} minutes.\n"
    )
    get_latest_weather_info()
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    setup_schedules_and_db()
