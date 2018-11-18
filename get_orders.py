"""
Project: Trading Engine
Author: Adish Jain
Date: 11/16/2018
"""
import pandas as pd
import falcon
import json
from datetime import datetime
from list_orders import ListOrders

"""
Handles POST requests to take order information from the /orders endpoint and
store it in memory
"""
class GetOrders:
    """
    Initializes an instance of the GetOrders class
    Parameters:
        1) db: an instance of the database class
        2) app: an instance of the app
    """
    def __init__(self, db, app):
        self.db = db
        self.firstOrder = True
        self.app = app

    """
    Handles GET requests at the /orders endpoint
    Parameters:
        1) request: represents a client’s HTTP request
        2) response: represents an HTTP response to a client request
    """
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

    """
    Handles POST requests at the /orders endpoint by taking in JSON input, doing
    matching logic, and storing information into database instance.
    Parameters:
        1) request: represents a client’s HTTP request
        2) response: represents an HTTP response to a client request
    """
    def on_post(self, request, response):
        response.status = falcon.HTTP_200

        # Try to read JSON input; Catch value-error for malformed input
        try:
            data = json.loads(request.stream.read())
            actual_data = data["data"]
            trader_id = actual_data["traderId"]
            orders_list = actual_data["orders"]
            df = pd.DataFrame.from_dict(orders_list, orient='columns')
            df["orderTime"] = [str(datetime.now())] * len(df)
            df["status"] = ["open"] * len(df)
            df["trader"] = [trader_id] * len(df)
            df["use"] = ["yes"] * len(df)
            new_order = df

            # Order-Matching
            if not self.firstOrder:
                all_existing_orders = pd.DataFrame()
                for d in self.db.get_orders():
                    all_existing_orders = all_existing_orders.append(d)
                for i in range(0, len(new_order)):
                    potential_matches =
                        all_existing_orders[(all_existing_orders['symbol'] == new_order.iloc[i]['symbol']) &
                                            (all_existing_orders['orderType'] != new_order.iloc[i]['orderType']) &
                                            (all_existing_orders['use'] == "yes") &
                                            (all_existing_orders['trader'] != trader_id) &
                                            (all_existing_orders['status'] != 'filled')]
                    if not potential_matches.empty:
                        potential_matches["distance"] = new_order.iloc[i]["quantity"] - list(potential_matches["quantity"])
                        potential_matches = potential_matches.reindex(potential_matches.distance.abs().sort_values().index)
                        potential_matches = potential_matches[potential_matches["distance"] == potential_matches.iloc[0]["distance"]]
                        potential_matches.sort_values(by="orderTime", inplace=True)
                        match = potential_matches.iloc[0]
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

            # Check if trader-ID is already in database. If not, we add it.
            if self.db.containsID(trader_id) == -1:
                self.db.add_trader(trader_id)
                self.db.add_order(new_order)
                list_orders = ListOrders(self.db, trader_id)
                self.app.add_route('/orders/' + trader_id, list_orders)
            else:
                existing_df = self.db.get_orders()[self.db.containsID(trader_id)]
                new_df = existing_df.append(new_order)
                self.db.get_orders()[self.db.containsID(trader_id)] = new_df
            response.body = json.dumps({'Order processed for':trader_id})
        except:
            response.body = json.dumps({'Error':"Order is malformed"})
