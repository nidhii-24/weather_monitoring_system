import os

# List of Indian metros
CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]
OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# a list of temperature units.
TEMP_UNIT_CELSIUS = "Celsius"
TEMP_UNIT_FAHRENHEIT = "Fahrenheit"
TEMP_UNIT_KELVIN = "Kelvin"
ALLOWED_TEMP_UNITS = [TEMP_UNIT_CELSIUS, TEMP_UNIT_FAHRENHEIT, TEMP_UNIT_KELVIN]

DB_CONFIG = {
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'yourpassword'),
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'weatherdb'),
}

OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'your_api_key')

# Default alert thresholds
ALERT_THRESHOLDS = {
    'city': 'London',
    'threshold': 35.0,
    'unit': 'Celsius',
    'consecutive_updates': 2,
}

# Retrieval and cleanup intervals
RETRIEVAL_INTERVAL = int(os.environ.get('RETRIEVAL_INTERVAL', '30'))  # in minutes
CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', '24'))      # in hours
