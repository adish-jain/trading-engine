"""
Project: Trading Engine
Author: Adish Jain
Date: 11/16/2018
"""
import falcon
import pandas as pd

"""
A database system which manages order and trader information for a session
"""
class Database:
    """
    Initializes an instance of the Database class
        self.traders: array of trader_ids
        self.orders: array of dataframes
    self.traders and self.orders are index-matched
    """
    def __init__(self):
        self.traders = []
        self.orders = []

    """
    Adds a trader_id to traders
    Parameters:
        1) traderid: the traderid to add
    """
    def add_trader(self, traderid):
        self.traders.append(traderid)

    """
    Returns traders
    """
    def get_traders(self):
        return self.traders

    """
    Adds a dataframe to orders
    Parameters:
        1) df: the dataframe to add
    """
    def add_order(self, df):
        self.orders.append(df)

    """
    Returns orders
    """
    def get_orders(self):
        return self.orders

    """
    Checks if traderid is contained in traders. Returns index, else -1.
    Parameters:
        1) traderid: the traderid for which we are searching
    """
    def containsID(self, traderid):
        if traderid in self.traders:
            return self.traders.index(traderid)
        else:
            return -1
