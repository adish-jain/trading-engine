'''
Project: Trading Engine
Author: Adish Jain
Date: 11/16/2018
'''
import pandas as pd
import falcon
import json
from datetime import datetime
from list_orders import ListOrders


class GetOrders:
    def __init__(self, db, app):
        self.db = db
        self.firstOrder = True
        self.app = app

    def on_get(self, request, response):
        orders = \
                    {
                        'error':
                        {
                            'status': "No pending orders",
                            'check': "Place an order by using a POST protocol"
                        }
                    }

        response.media = orders
        response.status = falcon.HTTP_200

    def on_post(self, request, response):
        response.status = falcon.HTTP_200
        try:
            data = json.loads(request.stream.read())
            actual_data = data["data"]
            trader_id = actual_data["traderId"] #string representing trader-ID
            orders_list = actual_data["orders"]
            df = pd.DataFrame.from_dict(orders_list, orient='columns') #dataframe representing new order
            df["orderTime"] = [str(datetime.now())] * len(df)
            df["status"] = ["open"] * len(df)
            df["trader"] = [trader_id] * len(df)
            df["use"] = ["yes"] * len(df)
            new_order = df #dataframe of new order
            #Order matching - right now only case where buy/sell amounts are exactly equal
            if not self.firstOrder:
                all_existing_orders = pd.DataFrame() #a dataframe of all existing orders that aren't from this trader
                for d in self.db.get_orders():
                    all_existing_orders = all_existing_orders.append(d)

                for i in range(0, len(new_order)):
                    potential_matches = all_existing_orders[(all_existing_orders['symbol'] == new_order.iloc[i]['symbol']) &
                                        (all_existing_orders['orderType'] != new_order.iloc[i]['orderType']) &
                                        (all_existing_orders['use'] == "yes") &
                                        (all_existing_orders['trader'] != trader_id) &
                                        (all_existing_orders['status'] != 'filled')] #all existing orders that match criteria
                    if not potential_matches.empty:
                        potential_matches["distance"] = new_order.iloc[i]["quantity"] - list(potential_matches["quantity"])
                        potential_matches = potential_matches.reindex(potential_matches.distance.abs().sort_values().index) #Orders by distance = new_order - existing_order
                        potential_matches = potential_matches[potential_matches["distance"] == potential_matches.iloc[0]["distance"]] #Keeps only those matches in first distance group
                        potential_matches.sort_values(by="orderTime", inplace=True)
                        match = potential_matches.iloc[0] #the first existing order (in time) which was placed which minimizes distance
                        matching_trader = match["trader"]
                        index_of_matching_trader = self.db.containsID(matching_trader)
                        df_of_matching_trader = self.db.get_orders()[index_of_matching_trader]
                        symbol = df_of_matching_trader["symbol"] == match["symbol"]
                        orderType = df_of_matching_trader["orderType"] == match["orderType"]
                        quantity = df_of_matching_trader["quantity"] == match["quantity"]
                        status = df_of_matching_trader["status"] == match["status"]
                        idx = df_of_matching_trader[(symbol) & (orderType) & (quantity) & (status)].index[0]
                        if match["distance"] == 0:
                            df_of_matching_trader.loc[idx, "status"] = "filled"
                            new_order.loc[i, "status"] = "filled"
                            df_of_matching_trader.loc[idx, "use"] = "no"
                            new_order.loc[i, "use"] = "no"
                        elif new_order.iloc[i]["orderType"] == "buy" and match["distance"] > 0:
                            df_of_matching_trader.loc[idx, "status"] = "filled"
                            new_order = new_order.append({"symbol":new_order.iloc[i]['symbol'],
                                                          "orderType":new_order.iloc[i]['orderType'],
                                                          "orderTime":new_order.iloc[i]['orderTime'],
                                                          "use":"yes",
                                                          "quantity":match["distance"],
                                                          "trader":trader_id,
                                                          "status":"partially_filled"}, ignore_index=True)
                            df_of_matching_trader.loc[idx, "use"] = "no"
                            new_order.loc[i, "use"] = "no"
                        elif new_order.iloc[i]["orderType"] == "buy" and match["distance"] < 0:
                            df_of_matching_trader = df_of_matching_trader.append({"symbol":match['symbol'],
                                                                                  "orderType":match["orderType"],
                                                                                  "orderTime":match['orderTime'],
                                                                                  "use":"yes",
                                                                                  "quantity":-match["distance"],
                                                                                  "trader":match["trader"],
                                                                                  "status":"partially_filled"}, ignore_index=True)
                            new_order.loc[i, "status"] = "filled"
                            df_of_matching_trader.loc[idx, "use"] = "no"
                            new_order.loc[i, "use"] = "no"
                        elif new_order.iloc[i]["orderType"] == "sell" and match["distance"] > 0:
                            df_of_matching_trader.loc[idx, "status"] = "filled"
                            new_order = new_order.append({"symbol":new_order.iloc[i]['symbol'],
                                                          "orderType":new_order.iloc[i]['orderType'],
                                                          "orderTime":new_order.iloc[i]['orderTime'],
                                                          "use":"yes",
                                                          "quantity":match["distance"],
                                                          "trader":trader_id,
                                                          "status":"partially_filled"}, ignore_index=True)
                            df_of_matching_trader.loc[idx, "use"] = "no"
                            new_order.loc[i, "use"] = "no"
                        elif new_order.iloc[i]["orderType"] == "sell" and match["distance"] < 0:
                            df_of_matching_trader = df_of_matching_trader.append({"symbol":match['symbol'],
                                                                                  "orderType":match["orderType"],
                                                                                  "orderTime":match['orderTime'],
                                                                                  "use":"yes",
                                                                                  "quantity":-match["distance"],
                                                                                  "trader":match["trader"],
                                                                                  "status":"partially_filled"}, ignore_index=True)
                            new_order.loc[i, "status"] = "filled"
                            df_of_matching_trader.loc[idx, "use"] = "no"
                            new_order.loc[i, "use"] = "no"

                        self.db.get_orders()[index_of_matching_trader] = df_of_matching_trader

            self.firstOrder = False
            #Checks if trader-ID is already in database. If not, we add. Otherwise, append new order to existing one.
            if self.db.containsID(trader_id) == -1: #trader-ID not already in list
                self.db.add_trader(trader_id)
                self.db.add_order(new_order)
                list_orders = ListOrders(self.db, trader_id) # one for each trader
                self.app.add_route('/orders/' + trader_id, list_orders)
            else:
                existing_df = self.db.get_orders()[self.db.containsID(trader_id)]
                new_df = existing_df.append(new_order) #append new df to existing df for trader
                self.db.get_orders()[self.db.containsID(trader_id)] = new_df #replace df in database
            response.body = json.dumps({'Order processed for':trader_id})
        except:
            response.body = json.dumps({'Error':"Order is malformed"})
