'''
Project: Trading Engine
Author: Adish Jain
Date: 11/16/2018
'''
import falcon
import pandas as pd

class Database:
    def __init__(self):
        self.traders = [] #list of trader ids
        self.orders = [] #list of dataframes which represent traders' orders

    def add_trader(self, traderid):
        self.traders.append(traderid)

    def get_traders(self):
        return self.traders

    def add_order(self, df):
        self.orders.append(df)

    def get_orders(self):
        return self.orders

    def containsID(self, traderid): #-1 if not, otherwise returns index
        if traderid in self.traders:
            return self.traders.index(traderid)
        else:
            return -1
