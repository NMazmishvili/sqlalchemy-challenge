# Import the dependencies.
from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from scipy import stats
import numpy as np
import pandas as pd
import datetime as dt


#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    print("Server received request for home page...")
    return (f"Welcome to my weather station page!<br/>"
            f"Available Routes:<br/>"
            f"/api/v1.0/precipitation<br/>"
            f"/api/v1.0/stations<br/>"
            f"/api/v1.0/tobs<br/>"
            f"<br/>"
            f"<br/>"
            f"For the two below dynamic routes please use date range: 2010-01-01 to 2017-08-23<br/>"
            f"/api/v1.0/start_date/<start><br/>"
            f"/api/v1.0/start_date/<start_date>/end_date/<end_date>"
        )

# Precipitation
year_ago_date = dt.date(2017,8,23) - dt.timedelta(days=365)

year_ago_data = session.query(Measurement.date,Measurement.prcp).\
    filter(Measurement.date >= year_ago_date).\
    filter(Measurement.date <= dt.date(2017,8,23)).all()

precipitation = {}
for tuple in year_ago_data:
    precipitation[tuple[0]] = tuple[1]

@app.route("/api/v1.0/precipitation")
def precipitation_data():
    """Return the precipitation data as json"""
    return jsonify(precipitation)

# Stations
joined = session.query(Station.id,Measurement.station,Station.name,Station.latitude,Station.longitude,Station.elevation).join(Station, Measurement.station==Station.station).group_by(Measurement.station).order_by(Station.id).all()

stations_dict = {}
for tuple in joined:
     stations_dict[tuple[0]] = {
          'Station': tuple[1],
          'Name': tuple[2],
          'Latitude': tuple[3],
          'Longitude': tuple[4],
          'Elevation': tuple[5]
     }

@app.route("/api/v1.0/stations")
def stations_list():
    return jsonify(stations_dict)

# Tobs
year_ago_station_date = dt.date(2017,8,18) - dt.timedelta(days=365)

year_ago_station_data = session.query(Measurement.date,Measurement.tobs).\
    filter(Measurement.date >= year_ago_station_date).\
    filter(Measurement.date <= dt.date(2017,8,18)).\
    filter(Measurement.station == 'USC00519281').all()

temperature = {}
for tuple in year_ago_station_data:
    temperature[tuple[0]] = tuple[1]

@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature data for the most active station as json"""
    return jsonify(temperature)

# Start route
query_last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
range_last_date = query_last_date[0] #grabs the date text
query_first_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first()
range_first_date = query_first_date[0]

@app.route("/api/v1.0/start_date/<start_date>")
def calculate_temperatures_from_start_date(start_date):
    """
    Calculates TMIN, TAVG, and TMAX for dates between start_date and end_date (inclusive).

    Args:
        start_date (str): Start date in the format 'YYYY-MM-DD'.

    Returns:
        str: A formatted string with the calculated temperatures.
    """
    try:
        # Convert date strings to datetime.date objects
        start_date_obj = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
        #end_date_obj = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
        first_date_obj = dt.datetime.strptime(range_first_date, "%Y-%m-%d").date()
        last_date_obj = dt.datetime.strptime(range_last_date, "%Y-%m-%d").date()

        # Check if start_date and end_date are within the valid range
        if first_date_obj <= start_date_obj <= last_date_obj: #and first_date_obj <= end_date_obj <= last_date_obj:
            # Query for the temperatures based on the start and end dates
            temperature = session.query(Measurement.tobs).\
                filter(Measurement.date>=start_date_obj).all()#.\
                #filter(Measurement.date<=end_date_obj).all()
            # Calculate the min, mean, and max using the temperature from above query
            tmin = stats.tmin(temperature)
            tavg = stats.tmean(temperature)
            tmax = stats.tmax(temperature)

            return jsonify({"Result": f"Temperature summary from {start_date} to 2017-08-23: TMIN = {tmin[0]}°F, TAVG = {round(tavg,2)}°F, TMAX = {tmax[0]}°F"})
        else:
            return jsonify({"Error": "Start date is outside the valid range (2010-01-01 to 2017-08-23)."})
    except ValueError:
        return jsonify({"Invalid date format": "Please provide dates in the format 'YYYY-MM-DD'."})

#Start/End route
query_last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
range_last_date = query_last_date[0] #grabs the date text
query_first_date = session.query(Measurement.date).order_by(Measurement.date.asc()).first()
range_first_date = query_first_date[0]

@app.route("/api/v1.0/start_date/<start_date>/end_date/<end_date>")
def calculate_temperatures_from_start_to_end_date(start_date, end_date):
    """
    Calculates TMIN, TAVG, and TMAX for dates between start_date and end_date (inclusive).

    Args:
        start_date (str): Start date in the format 'YYYY-MM-DD'.
        end_date (str): End date in the format 'YYYY-MM-DD'.

    Returns:
        str: A formatted string with the calculated temperatures.
    """
    try:
        # Convert date strings to datetime.date objects
        start_date_obj = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = dt.datetime.strptime(end_date, "%Y-%m-%d").date()
        first_date_obj = dt.datetime.strptime(range_first_date, "%Y-%m-%d").date()
        last_date_obj = dt.datetime.strptime(range_last_date, "%Y-%m-%d").date()

        # Check if start_date and end_date are within the valid range
        if first_date_obj <= start_date_obj <= last_date_obj and first_date_obj <= end_date_obj <= last_date_obj:
            # Query for the temperatures based on the start and end dates
            temperature = session.query(Measurement.tobs).\
                filter(Measurement.date>=start_date_obj).\
                filter(Measurement.date<=end_date_obj).all()
            # Calculate the min, mean, and max using the temperature from above query
            tmin = stats.tmin(temperature)
            tavg = stats.tmean(temperature)
            tmax = stats.tmax(temperature)

            return jsonify({"Result": f"Temperature summary from {start_date} to {end_date}: TMIN = {tmin[0]}°F, TAVG = {round(tavg,2)}°F, TMAX = {tmax[0]}°F"})
        else:
            return jsonify({"Error": "Start date or end date is outside the valid range (2010-01-01 to 2017-08-23)."})
    except ValueError:
        return jsonify({"Invalid date format": "Please provide dates in the format 'YYYY-MM-DD'."})


if __name__ == "__main__":
    app.run(debug=True)