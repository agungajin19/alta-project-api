# Import
from flask import Blueprint
from flask_restful import Api, reqparse, Resource, marshal, inputs
from sqlalchemy import desc
from .model import Customers
from blueprints import db, app
from datetime import datetime
import json

# Import Authentication
from flask_jwt_extended import jwt_required, get_jwt_claims

# Creating blueprint
bp_customers = Blueprint('customers', __name__)
api = Api(bp_customers)

class CustomersResource(Resource):
    # Enable CORS
    def options(self, id=None):
        return {'status': 'ok'}, 200

api.add_resource(CustomersResource, '')