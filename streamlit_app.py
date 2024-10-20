import streamlit as st
from db.db_manager import (
    check_alerts_in_app,
    load_summary_data,
    update_user_config,
    get_latest_weather_data_for_city,
    initialise_tables  
)
from config import (
    ALLOWED_TEMP_UNITS,
    TEMP_UNIT_KELVIN,
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
)
from utils.temperature_utils import convert_temperature_series, convert_temperature
import plotly.express as px
import pandas as pd  # Ensure pandas is imported
from datetime import datetime  # For formatting the timestamp

def display_streamlit_app():
    initialise_tables()
    st.title("Weather Monitoring System")

    # User-configurable settings
    st.sidebar.subheader("Settings")
    selected_unit = st.sidebar.selectbox("Select Temperature Unit", ALLOWED_TEMP_UNITS)

    if selected_unit == TEMP_UNIT_CELSIUS:
        threshold_value = 35
    elif selected_unit == TEMP_UNIT_FAHRENHEIT:
        threshold_value = 95
    elif selected_unit == TEMP_UNIT_KELVIN:
        threshold_value = 308

    high_temp_threshold = st.sidebar.number_input(
        f"High Temperature Threshold ({selected_unit})", value=threshold_value
    )
    consecutive_updates = st.sidebar.number_input(
        "Consecutive Updates", min_value=1, value=2
    )

    summary_df = load_summary_data()

    if summary_df.empty:
        st.write("No data available for visualization.")
        return

    # Convert temperatures in the summary data
    summary_df["avg_temp"] = convert_temperature_series(
        summary_df["avg_temp"], selected_unit
    )
    summary_df["max_temp"] = convert_temperature_series(
        summary_df["max_temp"], selected_unit
    )
    summary_df["min_temp"] = convert_temperature_series(
        summary_df["min_temp"], selected_unit
    )

    # City selection
    cities = summary_df["city"].unique()
    selected_city = st.selectbox("Select City", cities)

    # Fetch and display the latest weather data for the selected city
    latest_data = get_latest_weather_data_for_city(selected_city)

    if latest_data:
        # Convert temperatures to the selected unit
        converted_temp = convert_temperature(latest_data.temp, selected_unit)
        converted_feels_like = convert_temperature(latest_data.feels_like, selected_unit)

        st.subheader("Latest Weather Data")
        data = {
            "Main Weather Condition": latest_data.main,
            f"Temperature ({selected_unit})": f"{converted_temp:.2f}",
            f"Feels Like ({selected_unit})": f"{converted_feels_like:.2f}",
            "Data Update Time": latest_data.dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
        df_latest = pd.DataFrame([data])
        st.table(df_latest)
    else:
        st.write("No latest data available for this city.")

    # Update user config so alerts can use the latest settings
    update_user_config(
        selected_city, high_temp_threshold, selected_unit, consecutive_updates
    )

    # Display Alerts
    st.subheader(f"Alerts for {selected_city}")
    alerts = check_alerts_in_app()
    if alerts:
        for alert in alerts:
            st.error(alert)
    else:
        st.write("No alerts for this city.")

    # Plot interactive temperature trends
    st.subheader(f"Interactive Temperature Trends for {selected_city}")
    city_summary = summary_df[summary_df["city"] == selected_city]
    if not city_summary.empty:
        fig = px.line(
            city_summary,
            x="date",
            y="avg_temp",
            title=f"Average Temperature Over Time in {selected_city}",
            labels={"avg_temp": f"Average Temperature ({selected_unit})"}
        )
        st.plotly_chart(fig)
    else:
        st.write("No summary data available for this city.")

    # Data Export - allow to download as csv
    st.subheader("Download Data")
    if not city_summary.empty:
        csv = city_summary.to_csv(index=False)
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name=f"{selected_city}_weather_data.csv",
            mime="text/csv",
        )
    else:
        st.write("No data available for download.")

if __name__ == "__main__":
    display_streamlit_app()
