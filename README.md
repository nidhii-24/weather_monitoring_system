# Weather Monitoring System

A real-time weather monitoring application built with Python, Streamlit, and PostgreSQL, containerized using Docker and Docker Compose.

## Features

- **Real-Time Data Fetching:** Retrieves weather data for multiple cities using the OpenWeather API.
- **Database Storage:** Stores weather data and daily summaries in a PostgreSQL database.
- **User Interface:** Provides a Streamlit web app for data visualization and interaction.
- **Alerts:** Users can set temperature thresholds to receive alerts.
- **Data Export:** Option to download weather data as CSV files.
- **Scheduled Tasks:** Automated data retrieval and cleanup operations.

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

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.
- OpenWeather API key. Sign up at [OpenWeather](https://openweathermap.org/) to obtain one.

## Setup Instructions

### **1. Clone the Repository**

```bash
git clone https://github.com/nidhii-24/weather_monitoring_system.git
cd WEATHER_MONITORING_SYSTEM
```

### **2. Build and Start the Docker Containers**

```bash
docker-compose up --build
```

This command builds the Docker images and starts the `web`, `worker`, and `db` services.

### **3. Access the Application**

Open your web browser and navigate to:

```
http://localhost:8501
```

## Usage

### **Settings Sidebar**

- **Select Temperature Unit:** Choose between Celsius, Fahrenheit, or Kelvin.
- **High Temperature Threshold:** Set the temperature threshold for alerts.
- **Consecutive Updates:** Specify the number of consecutive updates that must exceed the threshold to trigger an alert.

### **Latest Weather Data**

- Displays the most recent weather data for the selected city, including:
  - **Main Weather Condition**
  - **Temperature**
  - **Feels Like Temperature**
  - **Data Update Time**

### **Interactive Temperature Trends**

- **Select City:** Use the dropdown to select a city.
- **Graph:** View the average temperature over time for the selected city.
- **Interactivity:** Hover over the graph to see specific data points.

### **Alerts**

- Alerts are displayed if the temperature exceeds the set threshold for the specified number of consecutive updates.

### **Download Data**

- **Download as CSV:** Export the weather data for the selected city.

## Stopping the Application

To stop the application and remove the containers, run:

```bash
docker-compose down
```

## Troubleshooting

### **No Data Available for Visualization**

- **Possible Cause:** The application may not have collected enough data yet.
- **Solution:** Wait a few minutes for the worker service to fetch and process data.


### **Running Tests**

- Navigate to the project directory.
- Run tests using:

  ```bash
  python -m unittest discover tests
  ```

