import requests
import datetime
from config import OPENWEATHER_API_KEY, CITIES, OPENWEATHER_API_URL


def get_weather_data(city):
    """ """
    params = {"q": city, "appid": OPENWEATHER_API_KEY}
    response = requests.get(OPENWEATHER_API_URL, params=params,verify=False)
    if response.status_code == 200:
        data = response.json()
        weather_info = {
            "city": city,
            "main": data["weather"][0]["main"],
            "temp": data["main"]["temp"],  # Store in Kelvin
            "feels_like": data["main"]["feels_like"],  # Store in Kelvin
            # We can store in local timezone for better readability.
            # This works as all the cities we query are in the same timezone
            # IE - IST.
            "dt": datetime.datetime.fromtimestamp(data["dt"]),
        }
        return weather_info
    else:
        error_message = response.json().get("message", "No error message provided")
        print(
            f"Failed to get data for {city}. Error code: {response.status_code}. Message: {error_message}"
        )
        return None


def get_all_cities_weather():
    """
    simply iterate over all the cities and get weather for each of them.
    """
    weather_data = []
    for city in CITIES:
        data = get_weather_data(city)
        if data:
            weather_data.append(data)
    return weather_data
