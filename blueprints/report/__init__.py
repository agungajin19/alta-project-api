# Import
from flask import Blueprint
from flask_restful import Api, reqparse, Resource, marshal, inputs
from sqlalchemy import desc
from blueprints.products.model import Products
from blueprints.carts.model import Carts, CartDetail
from blueprints.employees.model import Employees
from blueprints.customers.model import Customers
from blueprints.inventories.model import Inventories, InventoryLog
from blueprints.stock_outlet.model import StockOutlet
from blueprints.recipes.model import Recipe
from blueprints.users.model import Users
from blueprints.outlets.model import Outlets
from blueprints import db, app
from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import json
import random
import re

# Import Authentication
from flask_jwt_extended import jwt_required, get_jwt_claims
from blueprints import user_required, dashboard_required, apps_required

# Creating blueprint
bp_report = Blueprint('report', __name__)
api = Api(bp_report)

class ProductReport(Resource):
    # Enable CORS
    def options(self, id_product=None):
        return {'status': 'ok'}, 200
    
    # Get product report
    @jwt_required
    @dashboard_required
    def get(self):
        # Get ID users and
        claims = get_jwt_claims()
        id_users = claims['id']

        # Prepare variable needed
        product_list = []
        total_sold = 0
        total_sales = 0

        # Take input from users
        parser = reqparse.RequestParser()
        parser.add_argument('name', location = 'args', required = False)
        parser.add_argument('category', location = 'args', required = False)
        parser.add_argument('id_outlet', location = 'args', required = False)
        parser.add_argument('start_time', location = 'args', required = False)
        parser.add_argument('end_time', location = 'args', required = False)
        parser.add_argument('total_sold_sort', location = 'args', required = False)
        parser.add_argument('total_sales_sort', location = 'args', required = False)
        args = parser.parse_args()

        # Get all products from specific owner
        products = Products.query.filter_by(deleted = False).filter_by(id_users = id_users)

        # ----- First Filter -----
        # By name
        if args['name'] != '' and args['name'] is not None:
            products = products.filter(Products.name.like('%' + args['name'] + '%'))
        
        # By category
        if args['category'] != '' and args['category'] is not None:
            products = products.filter_by(category = args['category'])

        # Search all transactions related to the products in specified outlet
        for product in products:
            # Prepare variable needed
            total_sales_of_product = 0
            total_sold_of_product = 0
            detail_transaction = CartDetail.query.filter_by(id_product = product.id)

            # ----- Second Filter -----
            # By date interval
            if args['start_time'] is not None and args['end_time'] is not None and args['start_time'] != '' and args['end_time'] != '':
                start_year = int(args['start_time'][6:10])
                start_month = int(args['start_time'][3:5])
                start_day = int(args['start_time'][0:2])
                end_year = int(args['end_time'][6:10])
                end_month = int(args['end_time'][3:5])
                end_day = int(args['end_time'][0:2])
                detail_transaction = detail_transaction.filter(CartDetail.updated_at >= datetime(start_year, start_month, start_day).replace(hour = 0, minute = 0, second = 0, microsecond = 0)).filter(CartDetail.updated_at <= datetime(end_year, end_month, end_day).replace(hour = 0, minute = 0, second = 0, microsecond = 0) + timedelta(days = 1))

            for detail in detail_transaction:
                # Check for related outlet
                related_cart = Carts.query.filter_by(deleted = True).filter_by(id = detail.id_cart).first()
                related_outlet = Outlets.query.filter_by(deleted = False).filter_by(id = related_cart.id_outlet).first()
                if related_outlet is None:
                    continue
                
                # ----- Third Filter -----
                # By outlet ID
                if args['id_outlet'] != '' and args['id_outlet'] is not None:
                    if related_outlet.id != int(args['id_outlet']):
                        continue
                
                # Calculate some values
                total_sold_of_product = total_sold_of_product + detail.quantity
                total_sales_of_product = total_sales_of_product + detail.total_price_product

            total_sales = total_sales + total_sales_of_product
            total_sold = total_sold + total_sold_of_product
            data = {
                'name': product.name,
                'category': product.category,
                'total_sold': total_sold_of_product,
                'total_sales': total_sales_of_product   
            }
            product_list.append(data)

        # ----- Sort -----
        # By total sales - desc
        if args['total_sales_sort'] == 'desc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_sales'] < product_list[index + 1]['total_sales']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        # By total sales - asc
        if args['total_sales_sort'] == 'asc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_sales'] > product_list[index + 1]['total_sales']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        # By total sold - desc
        if args['total_sold_sort'] == 'desc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_sold'] < product_list[index + 1]['total_sold']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        # By total sold - asc
        if args['total_sold_sort'] == 'asc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_sold'] > product_list[index + 1]['total_sold']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        result = {
            'total_sales': total_sales,
            'total_sold': total_sold,
            'detail': product_list
        }
        return result, 200

class HistoryReport(Resource):
    # Enable CORS
    def options(self, id_product=None):
        return {'status': 'ok'}, 200
    
    # Get history report
    @jwt_required
    @dashboard_required
    def get(self):
        # Get the owner
        claims = get_jwt_claims()
        id_users = claims['id']
        owner = Users.query.filter_by(id = id_users).first()

        # Prepare variable needed
        product_list = []
        total_items_sold = 0
        total_sales = 0
        tax_summary = 0

        # Take input from users
        parser = reqparse.RequestParser()
        parser.add_argument('name', location = 'args', required = False)
        parser.add_argument('id_outlet', location = 'args', required = False)
        parser.add_argument('start_time', location = 'args', required = False)
        parser.add_argument('end_time', location = 'args', required = False)
        parser.add_argument('total_sold_sort', location = 'args', required = False)
        parser.add_argument('total_sales_sort', location = 'args', required = False)
        args = parser.parse_args()

        # Get all transactions history from specific owner
        transactions = Carts.query.filter_by(deleted = True).filter_by(id_users = id_users)
        
        # ----- Filter by Date Interval -----
        if args['start_time'] is not None and args['end_time'] is not None and args['start_time'] != '' and args['end_time'] != '':
            start_year = int(args['start_time'][6:10])
            start_month = int(args['start_time'][3:5])
            start_day = int(args['start_time'][0:2])
            end_year = int(args['end_time'][6:10])
            end_month = int(args['end_time'][3:5])
            end_day = int(args['end_time'][0:2])
            transactions = transactions.filter(Carts.created_at >= datetime(start_year, start_month, start_day).replace(hour = 0, minute = 0, second = 0, microsecond = 0)).filter(Carts.created_at <= datetime(end_year, end_month, end_day).replace(hour = 0, minute = 0, second = 0, microsecond = 0) + timedelta(days = 1))

        # ----- Filter by Outlet -----
        if args['id_outlet'] is not None and args['id_outlet'] != '':
            transactions = transactions.filter_by(id_outlet = args['id_outlet'])
        
        # Looping through all transactions
        for transaction in transactions:
            detail_transaction = CartDetail.query.filter_by(id_cart = transaction.id)
            outlet = Outlets.query.filter_by(id = transaction.id_outlet).first()
            
            # Search for cashier name
            if transaction.id_employee == None or transaction.id_employee == '':
                cashier_name = owner.fullname
            else:
                # Search for the employee
                cashier = Employees.query.filter_by(id = transaction.id_employee).first()
                cashier_name = cashier.full_name

            for detail in detail_transaction:
                # Prepare the variable needed
                add_stock = True
                
                # ----- Filter by Product Name -----
                product = Products.query.filter_by(id = detail.id_product).first()
                if args['name'] is not None and args['name'] != '':
                    if not re.search(args['name'].lower(), product.name.lower()):
                        add_stock = False

                if add_stock == True:
                    total_items_sold = total_items_sold + detail.quantity
                    total_sales = total_sales + detail.total_price_product
                    tax_summary = int(tax_summary + ((outlet.tax * detail.total_price_product) / 100))
                    data = {
                        'date_time': transaction.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        'date': transaction.created_at.strftime("%Y-%m-%d"),
                        'time': transaction.created_at.strftime('%H:%M:%S'),
                        'outlet': outlet.name,
                        'cashier_name': cashier_name,
                        'product_name': product.name,
                        'total_items': detail.quantity,
                        'total_sales': detail.total_price_product
                    }
                    product_list.append(data)

        # ----- Sort -----
        # By total sales - desc
        if args['total_sales_sort'] == 'desc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_sales'] < product_list[index + 1]['total_sales']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        # By total sales - asc
        if args['total_sales_sort'] == 'asc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_sales'] > product_list[index + 1]['total_sales']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        # By total sold - desc
        if args['total_sold_sort'] == 'desc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_items'] < product_list[index + 1]['total_items']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        # By total sold - asc
        if args['total_sold_sort'] == 'asc':
            product_list_length = len(product_list)
            restart = True
            while restart:
                restart = False
                for index in range(product_list_length - 1):
                    if product_list[index]['total_items'] > product_list[index + 1]['total_items']:
                        dummy = product_list[index]
                        product_list[index] = product_list[index + 1]
                        product_list[index + 1] = dummy
                        restart = True

        result = {
            'total_items_sold': total_items_sold,
            'total_sales': total_sales,
            'tax_summary': tax_summary,
            'detail': product_list
        }

        return result, 200

class InventoryLogReport(Resource):
    # Enable CORS
    def options(self, id_product=None):
        return {'status': 'ok'}, 200
    
    # Get inventory log report
    @jwt_required
    @dashboard_required
    def get(self):
        # Get the owner
        claims = get_jwt_claims()
        id_users = claims['id']
        owner = Users.query.filter_by(id = id_users).first()

        # Prepare variable needed
        result = []

        # Take input from users
        parser = reqparse.RequestParser()
        parser.add_argument('name', location = 'args', required = False)
        parser.add_argument('id_outlet', location = 'args', required = False)
        parser.add_argument('type', location = 'args', required = False)
        parser.add_argument('start_time', location = 'args', required = False)
        parser.add_argument('end_time', location = 'args', required = False)
        parser.add_argument('amount_sort', location = 'args', required = False)
        args = parser.parse_args()

        # Get all inventories
        inventories = Inventories.query.filter_by(id_users = id_users)

        # ----- Filter by name -----
        if args['name'] is not None and args['name'] != '':
            inventories = inventories.filter(Inventories.name.like('%' + args['name'] + '%'))
        
        # Get all related stock outlet
        for inventory in inventories:
            stock_outlet_list = StockOutlet.query.filter_by(id_inventory = inventory.id)

            # ----- Filter by outlet -----
            if args['id_outlet'] != '' and args['id_outlet'] is not None:
                stock_outlet_list = stock_outlet_list.filter_by(id_outlet = args['id_outlet'])
        
            # Get all related logs
            for stock_outlet in stock_outlet_list:
                logs = InventoryLog.query.filter_by(id_stock_outlet = stock_outlet.id)
                
                # Get outlet
                outlet = Outlets.query.filter_by(id = stock_outlet.id_outlet).first()

                # ----- Filter by type -----
                if args['type'] is not None and args['type'] != '':
                    logs = logs.filter_by(status = args['type'])

                # ----- Filter by date -----
                if args['start_time'] is not None and args['end_time'] is not None and args['start_time'] != '' and args['end_time'] != '':
                    start_year = int(args['start_time'][6:10])
                    start_month = int(args['start_time'][3:5])
                    start_day = int(args['start_time'][0:2])
                    end_year = int(args['end_time'][6:10])
                    end_month = int(args['end_time'][3:5])
                    end_day = int(args['end_time'][0:2])
                    logs = logs.filter(InventoryLog.created_at >= datetime(start_year, start_month, start_day).replace(hour = 0, minute = 0, second = 0, microsecond = 0)).filter(InventoryLog.created_at <= datetime(end_year, end_month, end_day).replace(hour = 0, minute = 0, second = 0, microsecond = 0) + timedelta(days = 1))

                for log in logs:
                    # Prepare the data
                    data = {
                        'name': inventory.name,
                        'outlet': outlet.name,
                        'date': log.created_at.strftime('%Y-%m-%d'),
                        'time': log.created_at.strftime('%H:%M:%S'),
                        'type': log.status,
                        'amount': log.amount,
                        'last_stock': log.last_stock
                    }
                    result.append(data)
        
        # ----- Sort -----
        # Desc
        if args['amount_sort'] == 'desc':
            result_length = len(result)
            restart = True
            while restart:
                restart = False
                for index in range(result_length - 1):
                    if result[index]['amount'] < result[index + 1]['amount']:
                        dummy = result[index]
                        result[index] = result[index + 1]
                        result[index + 1] = dummy
                        restart = True

        # By total sales - asc
        if args['amount_sort'] == 'asc':
            result_length = len(result)
            restart = True
            while restart:
                restart = False
                for index in range(result_length - 1):
                    if result[index]['amount'] > result[index + 1]['amount']:
                        dummy = result[index]
                        result[index] = result[index + 1]
                        result[index + 1] = dummy
                        restart = True

        return result, 200

class CategoryReport(Resource):
    # Enable CORS
    def options(self, id_product=None):
        return {'status': 'ok'}, 200

    # Get category report
    @jwt_required
    @dashboard_required
    def get(self):
        claims = get_jwt_claims()
        
        # Take input from users
        parser = reqparse.RequestParser()
        parser.add_argument('start_time', location = 'args')
        parser.add_argument('end_time', location = 'args')
        parser.add_argument('total_sold_sort', location = 'args', required = False)
        parser.add_argument('total_sales_sort', location = 'args', required = False)
        args = parser.parse_args()

        # Setting input time
        time = datetime.now().strftime("%d-%m-%Y")
        today = datetime(int(time[6:10]),int(time[3:5]),int(time[0:2]))
        start = today
        end = today + relativedelta(days = +1)
        if args['start_time'] is not None and args['end_time'] is not None and args['start_time'] != "" and args['end_time'] != "":
            start_time = args['start_time']
            start = datetime(int(start_time[6:10]),int(start_time[3:5]),int(start_time[0:2]))
            end_time = args['end_time']
            end = datetime(int(end_time[6:10]),int(end_time[3:5]),int(end_time[0:2]))
            end = end + relativedelta(days = +1)
            if end <= start :
                return {"message" : "Inputan Anda salah"}, 400

        # Prepare variable needed
        categories = []
        category_list = []
        total_quantity_category = 0
        total_price_category = 0

        qry_product = Products.query.filter_by(id_users = claims['id']).all()
        for product in qry_product:
            if product.category not in categories:
                categories.append(product.category)
        qry_cart = Carts.query.filter_by(id_users = claims['id']).all()
        for category in categories: 
            qry_product = Products.query.filter_by(id_users = claims['id']).filter_by(category = category).all()
            total_quantity = 0
            total_product = 0
            total_price = 0
            for product in qry_product:
                total_product = total_product + 1
                if qry_cart is not None:
                    for cart in qry_cart:
                        create_at = cart.created_at
                        if start <= create_at and create_at <= end:
                            qry_cartdetail = CartDetail.query.filter_by(id_cart = cart.id).filter_by(id_product = product.id).first()
                            if qry_cartdetail is not None:
                                total_quantity = total_quantity + qry_cartdetail.quantity
                    total_price = total_price + (product.price * total_quantity)
            data = {
                'category': category,
                'total_product': total_product,
                'total_sold': total_quantity,
                'total_sales': total_price
            }
            total_quantity_category = total_quantity_category + total_quantity
            total_price_category = total_price_category + total_price
            category_list.append(data)

        # ----- Sort -----
        # By total sales - desc
        if args['total_sales_sort'] == 'desc':
            category_list_length = len(category_list)
            restart = True
            while restart:
                restart = False
                for index in range(category_list_length - 1):
                    if category_list[index]['total_sales'] < category_list[index + 1]['total_sales']:
                        dummy = category_list[index]
                        category_list[index] = category_list[index + 1]
                        category_list[index + 1] = dummy
                        restart = True

        # By total sales - asc
        if args['total_sales_sort'] == 'asc':
            category_list_length = len(category_list)
            restart = True
            while restart:
                restart = False
                for index in range(category_list_length - 1):
                    if category_list[index]['total_sales'] > category_list[index + 1]['total_sales']:
                        dummy = category_list[index]
                        category_list[index] = category_list[index + 1]
                        category_list[index + 1] = dummy
                        restart = True

        # By total sold - desc
        if args['total_sold_sort'] == 'desc':
            category_list_length = len(category_list)
            restart = True
            while restart:
                restart = False
                for index in range(category_list_length - 1):
                    if category_list[index]['total_items_sold'] < category_list[index + 1]['total_items_sold']:
                        dummy = category_list[index]
                        category_list[index] = category_list[index + 1]
                        category_list[index + 1] = dummy
                        restart = True

        # By total sold - asc
        if args['total_sold_sort'] == 'asc':
            category_list_length = len(category_list)
            restart = True
            while restart:
                restart = False
                for index in range(category_list_length - 1):
                    if category_list[index]['total_items_sold'] > category_list[index + 1]['total_items_sold']:
                        dummy = category_list[index]
                        category_list[index] = category_list[index + 1]
                        category_list[index + 1] = dummy
                        restart = True

        result = {
            'category_list': category_list,
            "total_items_sold" : total_quantity_category,
            "total_sales" : total_price_category
        }

        return result, 200

class OutletReport(Resource):
    # Enable CORS
    def options(self, id_product=None):
        return {'status': 'ok'}, 200

    # Get category report
    @jwt_required
    @dashboard_required
    def get(self):
        claims = get_jwt_claims()
        
        # Take input from users
        parser = reqparse.RequestParser()
        parser.add_argument('start_time', location = 'args')
        parser.add_argument('end_time', location = 'args')
        parser.add_argument('name_outlet', location = 'args')
        args = parser.parse_args()

        # setting input time
        time = datetime.now().strftime("%Y-%m-%d")
        today = datetime(int(time[6:10]),int(time[3:5]),int(time[0:2]))
        start = today
        end = today + relativedelta(days = +1)
        if args['start_time'] is not None and args['end_time'] is not None and  args['start_time'] != "" and args['end_time'] != "":
            start_time = args['start_time']
            start = datetime(int(start_time[6:10]),int(start_time[3:5]),int(start_time[0:2]))
            end_time = args['end_time']
            end = datetime(int(end_time[6:10]),int(end_time[3:5]),int(end_time[0:2]))
            end = end + relativedelta(days = +1)
            if end <= start :
                return {"massage" : "inputan anda salah"}, 401
        
        # Prepare variable needed
        result = []
        if args['name_outlet'] is None or args['name_outlet'] ==     "":
            qry_outlet = Outlets.query.filter_by(id_user = claims['id']).all()
            while start < end: 
                amount_sales = 0
                number_transaction = 0
                for outlet in qry_outlet:
                    qry_cart = Carts.query.filter_by(id_users = claims['id']).filter_by(id_outlet = outlet.id).all()
                    if qry_cart is not None:
                        for carts in qry_cart:
                            create_at = carts.created_at
                            interval = start + relativedelta(days = +1)
                            print(start, "dan", create_at, "dan", end)
                            if start <= create_at and create_at <= interval:
                                amount_sales = amount_sales + carts.total_payment
                                number_transaction = number_transaction + 1
                    if qry_cart is None:
                        amount_sales = amount_sales + 0
                    
                    data = {
                        "name_outlet" : outlet.name,
                        "time" : str(start),
                        "total_transaction" : number_transaction,
                        "total_price" : amount_sales
                    }
                    result.append(data)
                start = start + relativedelta(days = +1)
            return result, 200

        if args['name_outlet'] is not None:
            qry_outlet = Outlets.query.filter_by(id_user = claims['id']).filter_by(name = args['name_outlet']).first()
            while start < end: 
                amount_sales = 0
                number_transaction = 0
                qry_cart = Carts.query.filter_by(id_users = claims['id']).filter_by(id_outlet = qry_outlet.id).all()
                if qry_cart is not None:
                    for carts in qry_cart:
                        create_at = carts.created_at
                        interval = start + relativedelta(days = +1)
                        if start <= create_at and create_at <= interval:
                            amount_sales = amount_sales + carts.total_payment
                            number_transaction = number_transaction + 1
                if qry_cart is None:
                    amount_sales = amount_sales + 0
                
                data = {
                    "name_outlet" : qry_outlet.name,
                    "time" : str(start),
                    "total_transaction" : number_transaction,
                    "total_price" : amount_sales
                }
                result.append(data)
                start = start + relativedelta(days = +1)
            return result, 200

class ProfitReport(Resource):
    # Enable CORS
    def options(self, id_product=None):
        return {'status': 'ok'}, 200

    @jwt_required
    @dashboard_required
    def get(self):
        claims = get_jwt_claims()
        
        # Take input from users
        parser = reqparse.RequestParser()
        parser.add_argument('start_time', location = 'args')
        parser.add_argument('end_time', location = 'args')
        parser.add_argument('name_outlet', location = 'args')
        args = parser.parse_args()

        # setting input time
        time = datetime.now().strftime("%Y-%m-%d")
        today = datetime(int(time[6:10]),int(time[3:5]),int(time[0:2]))
        start = today
        end = today + relativedelta(days = +1)
        
        if args['start_time'] is not None and args['end_time'] is not None and  args['start_time'] != "" and args['end_time'] != "":
            start_time = args['start_time']
            start = datetime(int(start_time[6:10]),int(start_time[3:5]),int(start_time[0:2]))
            end_time = args['end_time']
            end = datetime(int(end_time[6:10]),int(end_time[3:5]),int(end_time[0:2]))
            end = end + relativedelta(days = +1)
            if end <= start :
                return {"massage" : "inputan anda salah"}, 401
        
        result = []
        if args['name_outlet'] is None:
            qry_outlet = Outlets.query.filter_by(id_user = claims['id']).all()
            qry_product = Products.query.filter_by(id_users = claims['id']).all()
            qry_inventory = Inventories.query.filter_by(id_users = claims['id']).all()
            while start < end: 
                for outlet in qry_outlet:
                    amount_sales = 0
                    number_discount = 0
                    total_price_inventory = 0
                    profit = 0
                    qry_cart = Carts.query.filter_by(id_users = claims['id']).filter_by(id_outlet = outlet.id).all()
                    if qry_cart is not None:
                        for carts in qry_cart:
                            price_inventory_cart = 0
                            create_at = carts.created_at
                            interval = start + relativedelta(days = +1)
                            if start <= create_at and create_at <= interval:
                                amount_sales = amount_sales + carts.total_payment
                                number_discount = number_discount + carts.total_discount
                                if qry_product is not None :
                                    for product in qry_product:
                                        price_inventory_product = 0
                                        qry_cartdetail = CartDetail.query.filter_by(id_cart = carts.id).filter_by(id_product = product.id).first()
                                        if qry_cartdetail is not None:
                                            if qry_inventory is not None:
                                                for inventory in qry_inventory:
                                                    qry_recipe = Recipe.query.filter_by(id_product = product.id).filter_by(id_inventory = inventory.id).first()
                                                    if qry_recipe is not None:
                                                        price_inventory_product = price_inventory_product + (qry_recipe.amount * inventory.unit_price)
                                            price_inventory_cart = price_inventory_cart + (price_inventory_product * qry_cartdetail.quantity)
                                total_price_inventory = total_price_inventory + price_inventory_cart

                                    
                    if qry_cart is None:
                        amount_sales = amount_sales + 0
                        number_discount = number_discount + 0
                        total_price_inventory = total_price_inventory + 0

                    profit = amount_sales - (number_discount + total_price_inventory)
                    data = {
                        "name_outlet" : outlet.name,
                        "time" : str(start),
                        "total_price_cart" : amount_sales,
                        "total_price_discount" : number_discount,
                        "total_price_inventory" : profit 
                    }
                    result.append(data)
                start = start + relativedelta(days = +1)
            return result, 200


api.add_resource(ProductReport, '/product-sales')
api.add_resource(CategoryReport, '/category')
api.add_resource(OutletReport, '/outlet-sales')
api.add_resource(ProfitReport, '/profit')
api.add_resource(HistoryReport, '/history')
api.add_resource(InventoryLogReport, '/inventory-log')