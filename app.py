import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite", echo=False)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

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
def welcome():
    return (
        f"Welcome to the Hawaii Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/temp/start/end"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last year"""
    # Calculate the date 1 year ago from last date in database
    prcp_results =  engine.execute('SELECT date, prcp FROM Measurement WHERE date BETWEEN "2016-08-23" AND "2017-08-23"').fetchall()

    # Query for the date and precipitation for the last year
    date = [prcp_results[0] for prcp_result in prcp_results[0:]]
    prcp = [prcp_results[1] for prcp_result in prcp_results[0:]]
    prcp_df= pd.DataFrame(prcp_results[0:], columns=['date', 'prcp'] )
    prcp_df.set_index('date', inplace=True, )

    # Dict with date as the key and prcp as the value
    precip = {date: prcp for date, prcp in prcp_df}
    return jsonify(precip)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    stations_list = session.query(Station.station).all()

    # Unravel results into a 1D array and convert to a list
    stations = list(np.ravel(stations_list))
    return jsonify(stations)


@app.route("/api/v1.0/tobs")
def temp_monthly():
    """Return the temperature observations (tobs) for previous year."""
    # Calculate the date 1 year ago from last date in database
    prev_year = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    # Query the primary station for all tobs from the last year
    most_active_station = 'USC00519281'
    yearly_temps = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active_station).\
    filter(func.strftime("%Y-%m-%d", Measurement.date) >= dt.date(2016, 8, 23)).all()

    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(yearly_temps))

    # Return the results
    return jsonify(temps)


@app.route("/api/v1.0/temp/<start>")
@app.route("/api/v1.0/temp/<start>/<end>")
def stats(start=None, end=None):
    """Return TMIN, TAVG, TMAX."""

    # Select statement
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    if not end:
        # calculate TMIN, TAVG, TMAX for dates greater than start
        results = session.query(*sel).\
            filter(Measurement.date >= start).all()
        # Unravel results into a 1D array and convert to a list
        temps = list(np.ravel(results))
        return jsonify(temps)

    # calculate TMIN, TAVG, TMAX with start and stop
    results = session.query(*sel).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()
    # Unravel results into a 1D array and convert to a list
    temps = list(np.ravel(results))
    return jsonify(temps)


if __name__ == '__main__':
    app.run()