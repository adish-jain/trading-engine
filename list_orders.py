"""
Project: Trading Engine
Author: Adish Jain
Date: 11/16/2018
"""
import pandas as pd
import falcon
import json

"""
Handles GET requests to extract information from the database and present it to
the /orders/<self.id>
"""
class ListOrders:
    """
    Initializes an instance of the ListOrders class
    Parameters:
        1) db: an instance of the database class
        2) trader_id: the associated trader_id to this ListOrders instance
    """
    def __init__(self, db, trader_id):
        self.db = db
        self.id = trader_id

    """
    Handles GET requests at the /orders/<self.id> endpoint
    Parameters:
        1) request: represents a client’s HTTP request
        2) response: represents an HTTP response to a client request
    """
    def on_get(self, request, response):
        index = self.db.get_traders().index(self.id)
        df = self.db.get_orders()[index]
        orders = df.to_json(orient="records")
        response.body = orders
        response.status = falcon.HTTP_200
