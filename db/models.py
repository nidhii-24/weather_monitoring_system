from sqlalchemy import (
    Column,
    Float,
    String,
    Integer,
    DateTime,
    PrimaryKeyConstraint,
)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


# WeatherData will store timeseries data fetched from the openweather
# API. It will be periodically cleaned out every 2 days.
class WeatherData(Base):
    __tablename__ = "weather_data"
    city = Column(String, nullable=False, primary_key=True)
    main = Column(String)
    temp = Column(Float)
    feels_like = Column(Float)
    dt = Column(DateTime, nullable=False, primary_key=True)


# DailySummary stores the information about the rolled up temperature
# aggregates of each day.
class DailySummary(Base):
    __tablename__ = "daily_summary"
    date = Column(DateTime, primary_key=True)
    city = Column(String, primary_key=True)
    avg_temp = Column(Float)
    max_temp = Column(Float)
    min_temp = Column(Float)
    dominant_condition = Column(String)


class UserConfig(Base):
    __tablename__ = "user_config"
    city = Column(String, nullable=False, primary_key=True)
    threshold = Column(Float, nullable=False, primary_key=True)
    unit = Column(String, nullable=False, primary_key=True)
    consecutive_updates = Column(Integer, nullable=False, primary_key=True)
