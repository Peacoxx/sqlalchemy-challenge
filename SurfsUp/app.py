from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import pandas as pd
import datetime as dt

#################################################
# Database Setup
#################################################

# Database path
db_path = '/Users/pamala/Documents/GitHub/sqlalchemy-challenge/SurfsUp/Resources/hawaii.sqlite'
# Create an engine to connect to the SQLite database
engine = create_engine(f"sqlite:///{db_path}")

# Reflect the tables into a new model
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################

# Initialize Flask
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    return (
        "Welcome to the Climate App API!<br/>"
        "Available Routes:<br/>"
        "/api/v1.0/precipitation<br/>"
        "/api/v1.0/stations<br/>"
        "/api/v1.0/tobs<br/>"
        "/api/v1.0/start<br/>"
        "/api/v1.0/start/end<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date 12 months ago from the last data point in the database
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = pd.to_datetime(most_recent_date)
    one_year_ago = most_recent_date - dt.timedelta(days=365)
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')

    # Query for the last 12 months of precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).filter(Measurement.date >= one_year_ago_str).all()

    # Convert the query results to a dictionary using date as the key and prcp as the value
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Query all stations
    stations_data = session.query(Station.station, Station.name).all()

    # Convert the query results to a list of dictionaries
    stations_list = [{"station": station, "name": name} for station, name in stations_data]

    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Calculate the date 12 months ago from the last data point in the database
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = pd.to_datetime(most_recent_date)
    one_year_ago = most_recent_date - dt.timedelta(days=365)
    one_year_ago_str = one_year_ago.strftime('%Y-%m-%d')

    # Query the temperature observations of the most-active station for the previous year
    most_active_station = session.query(Measurement.station).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).first()[0]
    tobs_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).filter(Measurement.date >= one_year_ago_str).all()

    # Convert the query results to a list of dictionaries
    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in tobs_data]

    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start=None, end=None):
    # Query to calculate TMIN, TAVG, TMAX
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # Query for start date only
        results = session.query(*sel).filter(Measurement.date >= start).all()
    else:
        # Query for start and end date range
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()

    # Convert the query results to a list of dictionaries
    temperature_data = [{"TMIN": tmin, "TAVG": tavg, "TMAX": tmax} for tmin, tavg, tmax in results]

    return jsonify(temperature_data)

if __name__ == "__main__":
    app.run(debug=True)
