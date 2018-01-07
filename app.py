from flask import Flask, request
from flask_restful import Resource, Api, abort
from flask_restful import reqparse
from flask_jsonpify import jsonify
from json import dumps
from datetime import timedelta
from dateutil.parser import parse
from docopt import docopt
from geopy import geocoders
from math import trunc
from tzlocal import get_localzone
import datetime
import pytz
import requests
import sys
import time

app = Flask(__name__)
api = Api(app)

API_KEY = 'l7xxb3dcccc4a5674bada48fc6fcf0946bc8'
USER_EXPERIENCE_KEY = 'AAAA3198-4545-46F4-9A05-BB3E868BEFF5'
BASE_URL = 'https://mobile.southwest.com/api/'
CHECKIN_EARLY_SECONDS = 5
CHECKIN_INTERVAL_SECONDS = 0.25
MAX_ATTEMPTS = 10


parser = reqparse.RequestParser()
parser.add_argument('reservation_id')
parser.add_argument('first_name')
parser.add_argument('last_name')

reservations = {
    '1': {
        'first_name': 'ming',
        'last_name': 'ling',
        'status': 'pending',
        'reservation_date': datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%h')
    },
    '2': {
        'first_name': 'ming',
        'last_name': 'ling',
        'status': 'pending',
        'reservation_date': datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%h')
    }
}

def abort_if_invalid_reservation_id(reservation_id):
    if reservation_id not in reservations:
        abort(404, message="invalid reservation number")

# Pulled from proxying the Southwest iOS App
headers = {'Host': 'mobile.southwest.com', 'Content-Type': 'application/json', 'X-API-Key': API_KEY, 'X-User-Experience-Id': USER_EXPERIENCE_KEY, 'Accept': '*/*'}

# You might ask yourself, "Why the hell does this exist?"
# Basically, there sometimes appears a "hiccup" in Southwest where things
# aren't exactly available 24-hours before, so we try a few times
def safe_request(url, body=None):
    attempts = 0
    while True:
        if body is not None:
            r = requests.post(url, headers=headers, json=body)
        else:
            r = requests.get(url, headers=headers)
        data = r.json()
        import ipdb; ipdb.set_trace()
        if 'httpStatusCode' in data and data['httpStatusCode'] in ['NOT_FOUND', 'BAD_REQUEST', 'FORBIDDEN']:
            attempts += 1
            print("StatusCode:" + data['httpStatusCode'] + ", Message: " + data['message'])
            if attempts > MAX_ATTEMPTS:
                sys.exit("Unable to get data, killing self")
            time.sleep(CHECKIN_INTERVAL_SECONDS)
            continue
        return data

def lookup_existing_reservation(number, first, last):
    # Find our existing record
    url = "{}mobile-misc/v1/mobile-misc/page/view-reservation/{}?first-name={}&last-name={}".format(BASE_URL, number, first, last)
    data = safe_request(url)
    return data['viewReservationViewPage']

def get_checkin_data(number, first, last):
    url = "{}mobile-air-operations/v1/mobile-air-operations/page/check-in/{}?first-name={}&last-name={}".format(BASE_URL, number, first, last)
    data = safe_request(url)
    return data['checkInViewReservationPage']

def checkin(number, first, last):
    data = get_checkin_data(number, first, last)
    info_needed = data['_links']['checkIn']
    url = "{}mobile-air-operations{}".format(BASE_URL, info_needed['href'])
    print("Attempting check-in...")
    return safe_request(url, info_needed['body'])['checkInConfirmationPage']

def schedule_checkin(flight_time, number, first, last):
    checkin_time = flight_time - timedelta(days=1)
    current_time = datetime.now(pytz.utc).astimezone(get_localzone())
    # check to see if we need to sleep until 24 hours before flight
    if checkin_time > current_time:
        # calculate duration to sleep
        delta = (checkin_time - current_time).total_seconds() - CHECKIN_EARLY_SECONDS
        # pretty print our wait time
        m, s = divmod(delta, 60)
        h, m = divmod(m, 60)
        print("Too early to check in.  Waiting {} hours, {} minutes, {} seconds".format(trunc(h), trunc(m), s))
        time.sleep(delta)
    data = checkin(number, first, last)
    for flight in data['flights']:
        for doc in flight['passengers']:
            print("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))

def auto_checkin(reservation_number, first_name, last_name):
    body = lookup_existing_reservation(reservation_number, first_name, last_name)

    # setup a geocoder
    # needed since Southwest no longer includes TZ information in reservations
    g = geocoders.GoogleV3()

    # Get our local current time
    now = datetime.now(pytz.utc).astimezone(get_localzone())
    tomorrow = now + timedelta(days=1)

    # find all eligible legs for checkin
    for leg in body['bounds']:
        # calculate departure for this leg
        airport = "{}, {}".format(leg['departureAirport']['name'], leg['departureAirport']['state'])
        takeoff = "{} {}".format(leg['departureDate'], leg['departureTime'])
        point = g.geocode(airport).point
        airport_tz = g.timezone(point)
        date = airport_tz.localize(datetime.strptime(takeoff, '%Y-%m-%d %H:%M'))
        if date > now:
            # found a flight for checkin!
            print("Flight information found, departing {} at {}".format(airport, date.strftime('%b %d %I:%M%p')))
            schedule_checkin(date, reservation_number, first_name, last_name)


class Reservation(Resource):
    """takes on a confirmation number for checkin and can also del a confirmation"""
    def get(self, reservation_id):
        abort_if_invalid_reservation_id(reservation_id)
        return reservations[reservation_id]

    def delete(self, reservation_id):
        abort_if_invalid_reservation_id(reservation_id)
        del reservations[reservation_id]
        return '', 204

class Reservations(Resource):
    """returns all reservations and post new reservations"""
    def get(self):
        return reservations

# api.add_resource(Checkin, '/reservation/')
api.add_resource(Reservation, '/reservation/<reservation_id>')
api.add_resource(Reservations, '/reservations')


if __name__ == '__main__':
    app.run(debug=True)
