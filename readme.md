# Trading Engine
In this project, I worked on developing a small web-based application using Docker and Python's Gunicorn and Falcon libraries to simulate a matching engine for stock trade. In brief, a matching engine is is a tool used in trading that matches people that want to buy stocks with those that want to sell them. The project was done as part of a coding challenge for Schonfeld, a New York-based hedge fund. There are a couple sections in this spec that'll help you understand how exactly my implementation works:  

1) Tools Used
2) Project Files
3) Understanding Flow
4) Matching Logic
5) Running the Program  
    5a. Building  
    5b. Testing
6) Final Thoughts 

## Tools Used
Here, I give a short breakdown of all the development tools and Python libraries I used in completing this project:  

1) Docker - To create and deploy the web application
2) Atom - To develop my Python code 
3) Falcon - To build the RESTful API
4) Gunicorn - To serve the Falcon framework
5) Insomnia - To test my API
6) Pandas - To handle data manipulations and storage of trader/order information
7) Python - To write the server-side matching logic

## Project Files
Here, I give a short breakdown of all the files in the project directory, and how they interact with each other. For a much more detailed look at this interaction, please refer to the *Understanding Flow* section.  

1) requirements.txt - Contains all dependencies (Falcon, Gunicorn, Pandas)
2) Dockerfile - Downloads all dependencies and builds the Docker image from which we can instantiate a container 
3) app.py - An entrypoint for our application and drives route configuration
4) get_orders.py - Handles POST requests to take order information from the /orders endpoint and store it in memory
5) list_orders.py - Handles GET requests to access order information for a specific trader and send it to the /orders/<trader-id> endpoint
6) database.py - A barebones database system which manages order and trader information for a session 

## Understanding Flow 

## Matching Logic
Here, I delineate the logic I implemented to match orders:

Matches are made only between orders that have the same `symbol` and opposite `orderType`. In other words, stock being traded must belong to the same company, and a "buy" order can only be matched with a "sell" order. At a high-level, there are only three possible cases when considering matching two orders:

1) `buy_order_quantity = sell_order_quantity`
2) `buy_order_quantity > sell_order_quantity`
3) `buy_order_quantity < sell_order_quantity`

To measure how different two quantities are, let us define a new metric, `distance = new_order_quantity - existing_order_quantity`. In trying to process a new order, this will allow us to quantify how close the new order is to existing orders. Notice, `distance` will take on different values according to the three cases we defined above. Namely:

1) if `new_order_quantity = existing_order_quantity`, then `distance` will be 0
2) if `new_order_quantity > existing_order_quantity`, then `distance` will be positive-valued
3) if `new_order_quantity > existing_order_quantity`, then `distance` will be negative-valued

Combining these three cases with the previous three cases gives us five more granular cases to account for:

1) `distance = 0` implying `buy_order_quantity = sell_order_quantity` implying both orders are filled
2) distance is positive-valued  

    2a. `new_order` is of `orderType` buy implying `buy_order_quantity > sell_order_quantity` implying `new_order status` will be `partially_filled` and `existing_order status` will be `filled`  
    
    2b. `new_order` is of `orderType` sell implying `buy_order_quantity < sell_order_quantity` implying `new_order status` will be `partially_filled` and `existing_order status` will be `filled`
3) distance is negative-valued  

    3a. `new_order` is of `orderType` buy implying `buy_order_quantity < sell_order_quantity` implying `new_order status` will be `filled` and `existing_order status` will be `partially_filled`  
    
    3b. `new_order` is of `orderType` sell implying `buy_order_quantity > sell_order_quantity` implying `new_order status` will be `filled` and `existing_order status` will be `partially_filled`

These five cases entirely enumerate all possibilities in the matching logic. Matching is event-driven, meaning that this matching logic will only be traversed when the event that a `new_order` is placed occurs. In other words, when a `new_order` is placed, we check all existing orders to determine the optimal `existing_order`, if any exists. Optimality of existing orders is weighed on two metrics: `distance` (how closely the `existing_order` satisfies, in quantity, our `new_order`) and `orderTime` (when the `existing_order` was placed, giving priority to earlier orders). 

Specifically, higher priority is given to orders of minimum `distance` away from the `new_order` we are trying to satisfy. If multiple existing orders achieve this same minimum `distance`, then we use a FIFO approach using the `orderTime` field to determine which of these potential existing orders we will match. 

## Running the Program
### Building 
After you have installed Docker, you can build the trading engine locally by following these steps:  

1) Navigate to the project directory
2) Check to make sure your port isn't already allocated. You can do this by running the command `docker container ls`. If this returns nothing, you're all set to go onto step 3. Otherwise, run `docker rm -f <image name>` to remove the existing allocation. 
3) Build by running `docker build .`. If you've done this correctly, you should see "Successfully built <image-id>.
4) Instantiate a container of the image you just built by running `docker run -d -p 8080:8080 <image-id>`. The `-d` flag will run the container in background and print out the container ID. The `-p` flag will publish the container's ports to the specified host. 
5) Now, if you run `docker container ls`, you should see a new Docker container appear, and you'll see it is bound to port `0.0.0.0:8080`. This means we can access the application on Localhost `127.0.0.1:8080`.

### Testing
After you have installed Insomnia, you can test the trading engine by following these steps:  

1) Open up Insomnia and specify the URL as http://127.0.0.1:8080/orders/ (Localhost + /orders endpoint). Change the input type to JSON and the HTTP request to GET. After sending this request, you should see the following:
```
    {
        "error":
        {
            "status": "No pending orders",
            "check": "Place an order by using a POST protocol"
        }
    }
```    
2) This error is shown because the /orders endpoint is meant to process JSON input which represents a trader's buy/sell orders, for which a POST request is more appropriate. Accordingly, change the HTTP request in Insomnia to POST and specify a JSON input following the model:
```
    {
        "data":
        {
            "traderId": <trader-id as a string>,
            "orders": [
                {
                    "symbol": <company1 symbol as a string>
                    "quantity": <integer>
                    "orderType": <"buy" or "sell">
                },
                {
                    "symbol": <company2 symbol as a string>
                    "quantity": <integer>
                    "orderType": <"buy" or "sell>"
                }
            ]
        }
    }
```  
3) After sending this POST request, the trader information you should see the following:
```
    {
        "error":
        {
            "Order processed for": <trader-id>,
        }
    }
```    
4) To check that the order has been processed, change the URL to http://127.0.0.1:8080/orders/{trader-id} and the HTTP request to GET, and you should something similar to the following:
```
    [
        {
            "orderType": <"buy" or "sell">
            "quantity": <integer>
            "symbol": <company1 symbol as a string>
            "orderTime": <time order was placed>
            "status": <"open">
            "trader": <trader-id>
            "use": <"yes">
        },
        {
            "orderType": <"buy" or "sell">
            "quantity": <integer>
            "symbol": <company2 symbol as a string>
            "orderTime": <time order was placed>
            "status": <"open">
            "trader": <trader-id>
            "use": <"yes">
        }
    ]
    
```   
5) Repeat steps 2 through 4 to add orders for other traders. As matches are made, you will see the `status` field of orders change to `partially_filled` or `filled` depending on the quantities of the matches made. 

## Final Thoughts 
At first glance, this project was hugely intimidating for me. Many of the tools and libraries I utilized throughout this project were ones I had never even heard of before, much less worked with. In that sense, there was quite a learning curve for me. 

In total, I spent four days fleshing this project out. To break it down by day:

- Day 1: *Understanding the Problem & Creating a Framework*  
    Was spent on familiarizing myself with the problem I had to solve, and then understanding the tools and libraries by which I could produce some solution. This meant a lot of Googling, watching Youtube tutorials, and reading plenty of documentation. Once I had reviewed HTTP protocols and had a solid grasp of Falcon and how it works, I began to shift gears to actually designing a framework which could solve the problem. This meant setting my problem in the Object-Oriented Paradigm, and understanding exactly what objects I was dealing with, how they interacted, and the extent of their interactions. No code was written on Day 1 except some very simple playing around.

- Day 2: *Processing & Storing Orders*   
    Once I conceptualized the framework, I began to actually write some code. I first went about solving the problem of how I could take JSON inputs and store it in memory. I further decomposed this problem into two parts: processing JSON inputs and storing data in memory.
