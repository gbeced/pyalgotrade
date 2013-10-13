Tutorial for using Twitter events in your trading strategies
============================================================

Twitter support depends on **tweepy** (https://github.com/tweepy/tweepy) so be sure
to have it installed before moving forward.

The goal of this short tutorial is to illustrate how to connect to Twitter to process events.
We will also be using a live BarFeed since backtesting on Twitter is not supported.

In order to connect to Twitter's API you'll need:
 * Consumer key
 * Consumer secret
 * Access token
 * Access token secret

Go to http://dev.twitter.com and create an app.  The consumer key and secret will be generated for you after that.
Then you'll need to create an access token under the "Your access token" section.

.. literalinclude:: ../samples/tutorial_twitter_mtgox.py

The code is doing 5 things:
 1. Creating a feed to connect to Twitter's public stream API and setting the proper filtering parameters.
 2. Creating a client to connect to MtGox. For papertrading purposes we only need to specify the currency to use.
 3. Creating a live feed that will build bars from the trades received through the client.
 4. Creating a broker for backtesting. The broker will charge a 0.6 % fee for each order.
 5. Running the strategy with the bars supplied by the feed and the backtesting broker. **Note that the strategy adds MtGox client and Twitter feed to the event dispatch loop**.

If you run this example you should see something like this:

.. literalinclude:: ../samples/tutorial_twitter_mtgox.output
