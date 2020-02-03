# Import
from flask import Blueprint
from flask_restful import Api, reqparse, Resource, marshal, inputs
from sqlalchemy import desc
from .model import Users
from blueprints import db, app
from datetime import datetime
import json

# Import Authentication
from flask_jwt_extended import jwt_required, get_jwt_claims

# Creating blueprint
bp_users = Blueprint('users', __name__)
api = Api(bp_users)

class RegisterUserResource(Resource):

    #enalble CORS
    def options(self,id=None):
        return{'status':'ok'} , 200

    # to keep the password secret
    policy = PasswordPolicy.from_names(
        length = 6,
        uppercase = 1,
        numbers = 1
    )

    # create user account
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('email', location = 'json', required = True)
        parser.add_argument('password', location = 'json', required = True)
        args = parser.parse_args()
        
        validation = self.policy.test(args['password'])
        if validation:
            errorList = []
            for item in validation:
                split = str(item).split('(')
                error, num = split[0], split[1][0]
                errorList.append("{err}(minimum {num})".format(err=error, num=num))
            message = "Please check your password: " + ', '.join(x for x in errorList)
            return {'message': message}, 422, {'Content-Type': 'application/json'}
        encrypted = hashlib.md5(args['password'].encode()).hexdigest()
        
        user = Users(args['email'], encrypted)
        db.session.add(user)
        db.session.commit()
        app.logger.debug('DEBUG : %s', user)
        
        return {'message' : "registration success !!!"},200,{'Content-Type': 'application/json'}

class UserResource(Resource):
    
    def options(self,id=None):
        return{'status':'ok'} , 200
        
    policy = PasswordPolicy.from_names(
        length = 6,
        uppercase = 1,
        numbers = 1
    )

    @jwt_required
    @user_required
    # showing user profile (himself)
    def get(self):
        claims = get_jwt_claims()
        qry = Users.query.filter_by(id = claims['id']).first()
        if qry.deleted == False:
            return marshal(qry, Users.response_fields), 200
        return {'message' : 'NOT_FOUND'}, 404

    def put(self):
        claims = get_jwt_claims()
        qry = Users.query.filter_by(id = claims['id']).first()
        parser = reqparse.RequestParser()

        parser.add_argument('fullname', location = 'json')
        parser.add_argument('password', location = 'json')
        parser.add_argument('phone_number', location = 'json')
        parser.add_argument('business_name', location = 'json')
        parser.add_argument('image', location = 'json')

        args = parser.parse_args()

        if args['password'] is not None:
            validation = self.policy.test(args['password'])
            if validation:
                errorList = []
                for item in validation:
                    split = str(item).split('(')
                    error, num = split[0], split[1][0]
                    errorList.append("{err}(minimum {num})".format(err=error, num=num))
                message = "Please check your password: " + ', '.join(x for x in errorList)
                return {'message': message}, 422, {'Content-Type': 'application/json'}
            encrypted = hashlib.md5(args['password'].encode()).hexdigest()
            qry.password = encrypted
        if args['fullname'] is not None:
            qry.fullname = args['fullname']
        if args['phone_number'] is not None:
            qry.number_phone = args['phone_number']
        if args['business_name'] is not None:
            qry.address = args['business_name']
        if args['image'] is not None:
            qry.image = args['image']

        db.session.commit()
        return marshal(qry, Users.response_fields), 200

api.add_resource(RegisterUserResource,'/user/register')
api.add_resource(UserResource,'/user/profile')