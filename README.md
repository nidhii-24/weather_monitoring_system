# Weather Monitoring System

A robust and scalable weather monitoring system that periodically fetches weather data, manages user configurations, and raises alerts based on predefined thresholds. The system leverages SQLAlchemy for database interactions, Streamlit for the user interface, and the `schedule` library to handle background scheduling tasks efficiently.

## Table of Contents

- [Weather Monitoring System](#weather-monitoring-system)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Architecture \& Design Decisions](#architecture--design-decisions)
    - [WeatherData Table Management](#weatherdata-table-management)
    - [Alerts management.](#alerts-management)
    - [Job Configuration \& Alert Mechanism](#job-configuration--alert-mechanism)
    - [Running the UI and the backend logic in one dockerfile.](#running-the-ui-and-the-backend-logic-in-one-dockerfile)
  - [Running instructions](#running-instructions)
    - [UTs](#uts)

## Features

- **Periodic Weather Data Retrieval:** Fetches the latest weather information at regular intervals.
- **Data Management:** Automatically cleans up old weather data to maintain database efficiency.
- **Alerting System:** Raises alerts based on user-defined temperature thresholds and consecutive updates.

## Architecture & Design Decisions

### WeatherData Table Management

The `WeatherData` table is central to storing time-series weather data fetched from the OpenWeather API. To ensure the database remains efficient and free from obsolete data, the system is designed to **regularly delete old entries**:

- **Periodic Cleanup:** A scheduled job runs every day to remove weather data entries older **2 days**. This is okay for a 5 minute interval, as the maximum size of the weather_data table can be 24 * 60 / 5 = 288 entries per city, per day.
- **Efficient Storage:** By deleting outdated data, the system prevents the `WeatherData` table from growing indefinitely, which could degrade performance over time.

This approach ensures that only relevant and recent weather data is retained, optimizing both storage and query performance.

### Alerts management.

Alerts will be triggered everytime a user:

- changes their configuration (either the temperature threshold, unit, city or consecutive_updates)
- everytime we read data from the weather API. This is so we raise an alert immediately after we get the latest values.

Since the user can change the value anytime, and the API job needs to know the latest values of the user configuration, we store the configuration in the postgres db too. This table, called `user_config` will only contain one entry, at any point of time.

When the weather API job runs, it will read the latest user configuration from the user_config table and then check for alerts with that particular configuration.

### Job Configuration & Alert Mechanism

The system employs background jobs to handle data retrieval and alerting:

- **Data Retrieval Job:** Fetches the latest weather information every **5 minutes**. This ensures that the system always has up-to-date weather data for analysis and alerting.
- **Clean up job:** runs every day to remove weather data entries older **2 days**.

### Running the UI and the backend logic in one dockerfile.

The most ideal way is to run two dockerfiles one for the streamlit app and
one for the backend scheduler - but as a more lightweight solution, I use
multiprocessing library to run two processes - one that spins up the streamlit
ui, and one that runs the weather API job. This allows us to get away with a single
docker file.

  `
## Running instructions

### UTs

UTs are defined in the folder `/test`. We use unittests to write it. Please run the command:
```bash
 python -m unittest discover -s test
```