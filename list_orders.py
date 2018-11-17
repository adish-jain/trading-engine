'''
Project: Trading Engine
Author: Adish Jain
Date: 11/16/2018
'''
import pandas as pd
import falcon
import json


class ListOrders:
    def __init__(self, db, trader_id):
        self.db = db
        self.id = trader_id

    def on_get(self, request, response):
        index = self.db.get_traders().index(self.id)
        df = self.db.get_orders()[index]
        orders = df.to_json(orient="records")
        response.body = orders
        response.status = falcon.HTTP_200
