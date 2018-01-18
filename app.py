from flask import Flask, request
from flask_restful import Resource, Api, abort
from flask_restful import reqparse
from flask_jsonpify import jsonify
from json import dumps
from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from docopt import docopt
from geopy import geocoders
from math import trunc
from tzlocal import get_localzone
import pytz
import requests
import sys
import time
import logging

app = Flask(__name__)
api = Api(app)

#API_KEY = 'l7xxb3dcccc4a5674bada48fc6fcf0946bc8'
API_KEY = 'l7xx12ebcbc825eb480faa276e7f192d98d1'
USER_EXPERIENCE_KEY = 'AAAA3198-4545-46F4-9A05-BB3E868BEFF5'
BASE_URL = 'https://mobile.southwest.com/api/'
CHECKIN_EARLY_SECONDS = 5
CHECKIN_INTERVAL_SECONDS = 0.25
MAX_ATTEMPTS = 1

parser = reqparse.RequestParser()
parser.add_argument('reservation_id')
parser.add_argument('first_name')
parser.add_argument('last_name')

reservations = {
    '111111': {
        'first_name': 'ming',
        'last_name': 'ling',
        'status': 'pending',
        'legs': [
            {
                'order': '1',
                'airport_code': 'DCA',
                'status': 'pending',
                'seat': '',
                'flight_time_local': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M'),
                'flight_time_utc': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M')
            },
            {
                'order': '2',
                'airport_code': 'BWI',
                'status': 'pending',
                'seat': '',
                'flight_time_local': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M'),
                'flight_time_utc': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M')
            }
        ]
    },
    'AAAAAA': {
        'first_name': 'ming',
        'last_name': 'ling',
        'status': 'pending',
        'legs': [
            {
                'order': '1',
                'airport_code': 'IAD',
                'status': 'pending',
                'seat': '',
                'flight_time_local': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M'),
                'flight_time_utc': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M')
            },
            {
                'order': '2',
                'airport_code': 'PDX',
                'status': 'pending',
                'seat': '',
                'flight_time_local': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M'),
                'flight_time_utc': datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M')
            }
        ]
    },
    'TKJPZC': {
        "first_name": "ming",
        "last_name": "ling",
        "legs": [
            {
                "airport_code": "Washington (Reagan National), DC",
                "flight_time_local": "2018-02-17 06:25",
                "flight_time_utc": "2018-02-17 11:25",
                "order": 1,
                "status": "pending"
            },
            {
                "airport_code": "Portland, OR",
                "flight_time_local": "2018-02-20 07:00",
                "flight_time_utc": "2018-02-20 15:00",
                "order": 2,
                "status": "pending"
            },
            {
                "airport_code": "San Diego, CA",
                "flight_time_local": "2018-02-23 14:40",
                "flight_time_utc": "2018-02-23 22:40",
                "order": 3,
                "status": "pending"
            }
        ],
        "status": "pending"
    }
}

logger = logging.getLogger('SWCheckin')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
utc = pytz.timezone('UTC')


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
        #import ipdb; ipdb.set_trace()
        if 'httpStatusCode' in data and data['httpStatusCode'] in ['NOT_FOUND', 'BAD_REQUEST', 'FORBIDDEN']:
            attempts += 1
            logger.debug("StatusCode:" + data['httpStatusCode'] + ", Message: " + data['message'])
            if attempts > MAX_ATTEMPTS:
                #sys.exit("Unable to get data, killing self")
                return body
            time.sleep(CHECKIN_INTERVAL_SECONDS)
            continue
        return data

def lookup_existing_reservation(number, first, last):
    # Find our existing record
    url = "{}mobile-misc/v1/mobile-misc/page/view-reservation/{}?first-name={}&last-name={}".format(BASE_URL, number, first, last)
    data = safe_request(url)
    if data is None:
        return data
    return data['viewReservationViewPage']

def get_checkin_data(number, first, last):
    url = "{}mobile-air-operations/v1/mobile-air-operations/page/check-in/{}?first-name={}&last-name={}".format(BASE_URL, number, first, last)
    data = safe_request(url)
    return data['checkInViewReservationPage']

def checkin(number, first, last):
    #data = get_checkin_data(number, first, last)
    #info_needed = data['_links']['checkIn']
    #url = "{}mobile-air-operations{}".format(BASE_URL, info_needed['href'])
    #logger.debug("Attempting check-in {} {} with reservation {}").format(first, last, number )
    #return safe_request(url, info_needed['body'])['checkInConfirmationPage']
    #data = safe_request(url, info_needed['body'])['checkInConfirmationPage']
    #for flight in data['flights']:
    #   for doc in flight['passengers']:
    #    logger.debug("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))
    #add to this info to the record
    #update reservations
    reservations[number]['status'] = 'Checked In'


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
        logger.debug("Too early to check in.  Waiting {} hours, {} minutes, {} seconds".format(trunc(h), trunc(m), s))
        time.sleep(delta)
    data = checkin(number, first, last)
    for flight in data['flights']:
        for doc in flight['passengers']:
            logger.debug("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))

def auto_checkin(reservation_number, first_name, last_name):
    body = lookup_existing_reservation(reservation_number, first_name, last_name)

    if body is None:
        return -1
    logger.debug("legs found, adding to record")
    # setup a geocoder
    # needed since Southwest no longer includes TZ information in reservations
    g = geocoders.GoogleV3()

    # Get our local current time
    #import ipdb; ipdb.set_trace()
    now = datetime.now(pytz.utc).astimezone(get_localzone())
    tomorrow = now + timedelta(days=1)

    # find all eligible legs for checkin
    reservations[reservation_number] = {'first_name': first_name, 'last_name': last_name, 'status': 'pending', 'legs': []}
    legcounter = 0
    for leg in body['bounds']:
        # calculate departure for this leg
        legcounter += 1
        airport = "{}, {}".format(leg['departureAirport']['name'], leg['departureAirport']['state'])
        takeoff = "{} {}".format(leg['departureDate'], leg['departureTime'])
        point = g.geocode(airport).point
        logger.debug("airport: %s, take off: %s, point: %s", airport, takeoff, point)

        airport_tz = g.timezone(point)
        date = airport_tz.localize(datetime.strptime(takeoff, '%Y-%m-%d %H:%M'))
        if date > now:
            # found a flight for checkin!
            logger.debug("Flight information found, departing {} at {}".format(airport, date.strftime('%Y-%m-%d %H:%M')))
            #add pending and datetime to reservation
            reservations[reservation_number]['legs'].append({'order': legcounter, 'airport_code': airport, 'flight_time_local':  datetime.strftime(date, '%Y-%m-%d %H:%M'),
            'flight_time_utc': datetime.strftime(date.astimezone(utc), '%Y-%m-%d %H:%M') , 'status': 'pending'})

            #leverage scheduler in PCF to schedule this reservation
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

    def post(self):
        logger.debug(" Reservations Post Event")
        args = parser.parse_args()
        reservation_id = args['reservation_id']
        if len(reservation_id) is not 6:
            return "invalid reservation number", 201
        first_name = args['first_name']
        last_name = args['last_name']
        if reservation_id in reservations:
            return "reservation is already in queue", 201
        response = auto_checkin(reservation_id, first_name, last_name )
        if response is -1:
            return "reservation code appears to be invalid", 404
        #reservations[reservation_id] = {'first_name': first_name, 'last_name': last_name}
        return reservations[reservation_id], 201

class Checkin(Resource):
    """takes on a confirmation number for checkin and can also del a confirmation"""
    def get(self, reservation_id):
        abort_if_invalid_reservation_id(reservation_id)
        data = checkin(reservations[reservation_id], reservations[reservation_id].get("first_name"), reservations[reservation_id].get("last_name") )
        for flight in data['flights']:
            for doc in flight['passengers']:
                logger.info("{} got {}{}!".format(doc['name'], doc['boardingGroup'], doc['boardingPosition']))
        return reservations[reservation_id], 201

    def post(self, reservation_id):
        logger.debug("Chekins Post Event")
        args = parser.parse_args()
        reservation = reservations[reservation_id]
        first_name = reservations[reservation_id]["first_name"]
        last_name = reservations[reservation_id]["last_name"]
        checkin(reservation, first_name, last_name)
        return ("looks good first name {} lastname {} and confirmation {}".format(first_name, last_name, reservation, ), 201)

api.add_resource(Reservation, '/reservations/<reservation_id>')
api.add_resource(Reservations, '/reservations/')
api.add_resource(Checkin, '/checkin/<reservation_id>')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
