import datetime
from flask import Flask, request
from flask_restful import Resource, Api, abort
from flask_restful import reqparse
from flask.ext.jsonpify import jsonify
from json import dumps

API_KEY = 'l7xxb3dcccc4a5674bada48fc6fcf0946bc8'
USER_EXPERIENCE_KEY = 'AAAA3198-4545-46F4-9A05-BB3E868BEFF5'
BASE_URL = 'https://mobile.southwest.com/api/'
CHECKIN_EARLY_SECONDS = 5
CHECKIN_INTERVAL_SECONDS = 0.25
MAX_ATTEMPTS = 10

app = Flask(__name__)
api = Api(app)

APIKeys = {
    'j3faajH7Mv': 'ming',
    'j3faajH7Mv12323': 'risa'
}

reservations = [
{
    'reservation_id': 1,
    'first_name': 'ming',
    'last_name': 'ling',
    'reservation_date': datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%h')
},
{
    'reservation_id': 2,
    'first_name': 'ming',
    'last_name': 'ling',
    'reservation_date': datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%h')
}
]

def abort_if_invalid_key(key):
    if key not in APIKeys:
        abort(404, message="invalid key")

parser = reqparse.RequestParser()
parser.add_argument('key')
parser.add_argument('first_name')
parser.add_argument('last_name')
parser.add_argument('reservation_number')


# Checkin
# takes on a confirmation number and attempts to check in via SW site
class Checkin(Resource):
    def get(self, key, first_name, last_name, reservation_number):
        abort_if_invalid_key(key)
        return TODOS[todo_id]


class Reservation(Resource):
    """Pending reservations"""
    def get(self, key):
        abort_if_invalid_key(key)
        return reservations


# api.add_resource(Checkin, '/reservation/')
api.add_resource(Reservation, '/reservations/<key>')


if __name__ == '__main__':
    app.run(debug=True)
