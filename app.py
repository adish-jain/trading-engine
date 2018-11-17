import falcon
from database import Database
from health_check import HealthCheck
from get_orders import GetOrders
from list_orders import ListOrders


APP = falcon.API()

#health_check_resource = HealthCheck()
db = Database()
#get_new_orders = GetOrders(db)
get_new_orders = GetOrders(db, APP)##ADDED THIS

#APP.add_route('/health', health_check_resource)#
#APP.req_options.auto_parse_form_urlencoded = True
APP.add_route('/orders', get_new_orders)
#traders = ["1", "2"]
#traders = db.get_traders() #returning an empty list
#for i in traders:
#    list_orders = ListOrders(db, i) # one for each trader
#    APP.add_route('/orders/' + i, list_orders)
