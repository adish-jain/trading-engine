# Trading Engine | Adish Jain
In this project, I worked on developing a small web-based application using Docker and Python's Gunicorn and Falcon libraries to simulate a matching engine for stock trade. In brief, a matching engine is a tool used in trading that matches people that want to buy stocks with those that want to sell them. The project was done as part of a coding challenge for Schonfeld, a New York-based hedge fund. There are a couple sections in this spec that'll help you understand how exactly my implementation works:  

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
8) Git(Hub) - To version control

## Project Files
Here, I give a short breakdown of all the files in the project directory, and how they interact with each other. For a much more detailed look at this interaction, please refer to the *Understanding Flow* section.  

1) requirements.txt - Contains all dependencies (Falcon, Gunicorn, Pandas)
2) Dockerfile - Downloads all dependencies and builds the Docker image from which we can instantiate a container 
3) app.py - An entrypoint for our application and drives route configuration
4) get_orders.py - Handles POST requests to take order information from the `/orders` endpoint and store it in memory
5) list_orders.py - Handles GET requests to access order information for a specific trader and send it to the `/orders/trader-id` endpoint
6) database.py - A barebones database system which manages order and trader information for a session 

## Understanding Flow 
Here, I walk through the flow of the program, and the interactions that occur between components of the program in much more depth:

### Dockerfile: Building a Container
The container is born through the Dockerfile, which downloads all dependencies specificed in requirements.txt and instantiates a Docker container. I won't go into the specifics of how the container is actually built, but please reference the *Building* section of *Running the Program* below if you would like to learn more about this. 

### app.py: Creating the Application
Once our Docker container exists, we instantiate our application and the database which will be used throughout this specific run of the application. We also instantiate an instance of our `GetOrders` class and link it to a new endpoint: `/orders`. We will use this instance of `GetOrders` to actually process trader/order information and store this data in memory. 

### database.py: Storing Order Information
Though this file does not see the center stage at any given part of our program, it is really doing all the heavy-lifting behind the scenes. It represents a barebones database class which has two key instance attributes: `traders` and `orders`. The former is an array of trader ids, each appended at the time that trader's order is processed, and the latter is an array of Pandas dataframes which contain orders specific to a trader. These two arrays are index-matched, which means the dataframes in `orders` correspond, by index, to the trader ids in `traders`. 
    
Using this database framework, I have a way to store order information specific to each trader, which is necessary for the /orders/trader-id endpoints. 

### get_orders.py: Processing & Matching Orders
Our `GetOrders` instance has attributes `self.db`, `self.firstOrder`, and `self.app`. The first represents the database instance we created in app.py, which we will eventually need to store information into. The second represents a Boolean gate which tells us whether we are processing the *first* order on this run of the application. If this is so, our processing runs a little differently than if we already have orders in our database. This is because the very first order cannot be matched with anything, as there is nothing to match it to. Finally, the last attribute represents the instance of the application we created in app.py, which we will need to add trader-specific endpoints later on in the program.

The `GetOrders` class supports two types of requests at the `/orders` endpoint: GET and POST:  
<p>The GET request simply shows a message to users to enter data using a POST protocol. Nothing special here.</p>
<p>The POST request is a little more involved. When a POST request is made with some JSON input, I begin by trying to read in the JSON     input and store it as a Python dictionary. If this reading fails, perhaps due to malformed input, I immediately throw an error to         the `/orders` endpoint to tell the user that their JSON needs to be revised.
    
If the input was indeed correctly read in, we then proceed to process and store it. We first extract the `trader_id` and the `orders_list` components from the input (there should only be one of each of these in the input JSON). From the list of orders, we construct a Pandas dataframe which will, from hereforth, be the structure we use to store order information specific to a trader. The dataframe has columns as follow: `orderType`, `quantity`, `symbol`, `orderTime`, `status`, `trader`, and `use`. Each record in the dataframe represents a specific order in the `order_list`. The first three columns are filled from the JSON input itself, which requires those fields to specify an order. The last three fields are created in processing in each order. `orderTime` represents the date/time at which an order was placed, `status` represents whether an order is `open`, `filled`, or `partially_filled`. All orders start as `open`. Finally, `use` represents whether an order is open for exchange. The necessity for this extra field is something I'll get into shortly.

As aforementioned, if an order is the first order being processed in a given run of the application, we proceed to simply add the `trader_id` and the `new_order` to our database instance. We also then create an instance of our `ListOrders` class, and associate it with a new endpoint: `/orders/trader-id`. Finally, we set `self.firstOrder` to `False` so that next time we don't proceed through this route.

In processing all orders which follow the first, we need to actually walk through our matching logic and see if any matches can be made with existing orders. I won't walk through the specifics of the matching logic here, but for more information on that, refer to the *Matching Logic* section below. In short, to actually do the matching, I consider all orders in aggregate. To do this, I simply take all the dataframes in `orders` (the database attribute) and put them together in one larger dataframe, which I then manipulate using the matching logic described below. 

Namely, once I have this large dataframe which represents `all_existing_orders`, I then iterate through each record in our `new_order` dataframe to try to find the best match (as defined by our matching logic). I won't get into the details here, as it is mostly some dry Pandas manipulations, but feel free to check the code out, as it is pretty self-explanatory. After I find a `match` for the `new_order`, I update the `new_order` dataframe to specify that whatever record was matched has been either `filled` or `partially_filled`. If the record is completely `filled`, this involves just changing the `status` field of that record. However, if it is only `partially_filled`, I actually create a new record in my `new_order` dataframe to represent this *new* order, which has only been partially filled. This means that two orders will exist with the same `orderType`, `symbol`, `orderTime`, and `trader` fields. The first of these will be the initial order, with status `open`, and the second will be the new order, with status `partially_filled` and decreased `quantity` depending on how much of the initial order was filled. 

This is why the `use` field is necessary. Because we have multiple records which actually represent the same order at different timesteps, we only want to consider the *most recent* version of that order. `use` is set to "yes" for only this version of the order, and "no" to all else, indicating whether or not the record can be used for matching future orders. 

Similar updates are also made to the record of the dataframe we used to match this new order.

After all the matching logic is done, we follow a path similar to the trivial case of the first order. However, we also check to make sure that `trader_id` does not yet already exist in our `traders` attribute of our database instance. If it does, we don't want to include their id twice, so we simply take the `new_order` and append it to the existing dataframe for the trader. If this is the trader's first trade, then we can simply add in their `trader_id` to `traders` and their `new_order` dataframe to `orders`. If it is the trader's firs trade, we also create an instance of our `ListOrders` class, and associate it with a new endpoint: `/orders/trader-id`.

### list_orders.py: Accessing Orders by Trader
We create ListOrders instances for each trader, and each instance has two attributes: `self.db` and `self.id`. The first is, again, the database instance we created in app.py, which we will need to access information from. The second represents the specific trader_id with which the ListOrders instance is associated. We will need this to access the correct information from our database.

Recall that our database instance has attributes `traders`, an array of trader-ids, and `orders`, an array of dataframes, and that these attributes are index-matched. All we need to do, then, is find index at which `self.id` exists in `traders`, and use that index to access the correct dataframe from `orders`. Because of the procedure we followed to store information in get_orders.py, we know that this dataframe represents the most updated version of orders for the given trader, and so we can simply display this dataframe in a JSON format upon a GET request.

    
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

1) Open up Insomnia and specify the URL as http://127.0.0.1:8080/orders/ (Localhost + `/orders` endpoint). Change the input type to JSON and the HTTP request to GET. After sending this request, you should see the following:
```
    {
        "error":
        {
            "status": "No pending orders",
            "check": "Place an order by using a POST protocol"
        }
    }
```    
2) This error is shown because the `/orders` endpoint is meant to process JSON input which represents a trader's buy/sell orders, for which a POST request is more appropriate. Accordingly, change the HTTP request in Insomnia to POST and specify a JSON input following the model:
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
    The first day was spent on familiarizing myself with the problem I had to solve, and then understanding the tools and libraries by which I could produce some solution. This meant a lot of Googling, watching Youtube tutorials, and reading plenty of documentation. Once I had reviewed HTTP protocols and had a solid grasp of Falcon and how it works, I began to shift gears to actually designing a framework which could solve the problem. This meant setting my problem in the Object-Oriented Paradigm, and understanding exactly what objects I was dealing with, how they interacted, and the extent of their interactions. No code was written on Day 1 except some very simple playing around.

- Day 2: *Processing & Storing Orders*   
    On the second day, once I conceptualized the framework, I began to actually write some code. I first went about solving the problem of how I could take JSON inputs and store it in memory. I further decomposed this problem into two parts: processing JSON inputs and storing data in memory.
    
    The first problem of processing JSON was easily solved once I discovered `request.stream.read()`, to which I could then apply `json.loads()` and have my data in a Python dictionary structure. The second problem required a lot more thinking. Namely, I was presented with trader ids and trader-specific order information, and had to come up with a way to store that information so that it was specific to each trader id, but also was aggregate so that I could look through all orders when trying to find a match.
    
    The solution I came up with was the database framework, with which I had a way to look at trader and order information from two perspectives: on a very granular level specific to each trader, and also on a more collective scale where I could consider all existing orders made.
    
- Day 3: *Developing the Matching Logic*  
    With the protocols to process order information, and a system to store it, I now I had to begin tackling the Goliath which was the matching logic. Of course, extensive work has been prior done in developing extremely advanced algorithms to support order matching. Attempting to code out one of these was not the point of this project. Instead, the point of this project was developing a framework into which one of these algorithms could fit. For this reason, I wanted to keep the matching logic relatively simple, but of course not *too* simple. 
    
    I first wrote out the code to tackle the case when orders are exactly the same in quantity. Therefore, a match would only be made if someone is buying exactly the amount which someone else is selling. This required manipulations of my dataframe, and a lot of reading up on Pandas documentation and StackOverflow, but was not super difficult to do. 
    
    After I had that base done, I began to build on it by thinking through the logic I wanted to eventually implement, and how I wanted to assign priorities to orders. What I eventually came up with has already been discussed in the *Matching Logic* section so I won't repeat it here, but coming up with such logic was a creative journey. What I mean by that is that this is exactly what people do when they conceive ideas that are applied on the daily: sit back and think through what works, and then see if it is feasible to implement. And just by doing this over and over, and optimizing a little bit here and there on each iteration, we, as a society, construct the advanced algorithms and concepts that are put to use everywhere in life. It's amazing.
    
- Day 4: *Testing, Error-Checking, and Quick Fixes*  
    After I had most of the code written out, the last day of work followed easily. This day was mostly spent wrapping up all the code, and doing a lot of testing. Though I was testing throughout the course of the project, this was less ad-hoc testing of specific modules, and more dedicated time to really ensure everything is working properly together. 
    
    Testing, of course, led to a lot of time spent debugging, accidentally breaking my project, and then rewinding and fixing. It was definitely a process. Because this was a framework I wasn't too familiar with, it was also difficult at times to understand what exactly was causing the program to break. There were so many variables, and so it was a long process to pinpoint exactly what was causing a specific issue. But with each bug I ran into, I learned something new about the libraries and the framework with which I was dealing, and so I guess the best way to learn really is just to get your hands dirty.
    
    The last few hours were spent writing up this entire write-up, which is perhaps just as important as the last few days combined. **For if you cannot convey what you've created, you don't add to the sum of human knowledge**.
