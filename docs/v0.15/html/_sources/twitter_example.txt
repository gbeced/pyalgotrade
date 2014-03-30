Twitter Example
===============

This goal of this simple example is to show you how to put all the pieces together to incorporate
Twitter events in a strategy.
We will be using Bitstamp's live feed since backtesting with Twitter is not supported so please
take a look at the :ref:`bitstamp-tutorial-label` section before moving forward.

In order to connect to Twitter's API you'll need:
 * Consumer key
 * Consumer secret
 * Access token
 * Access token secret

Go to http://dev.twitter.com and create an app.  The consumer key and secret will be generated for you after that.
Then you'll need to create an access token under the "Your access token" section.

The key things to highlight are:

 1. We're using :class:`pyalgotrade.strategy.BaseStrategy` instead of :class:`pyalgotrade.strategy.BacktestingStrategy`
    as the base class. This is not a backtest.
 2. The :class:`pyalgotrade.twitter.feed.TwitterFeed` instance has to be included in the strategy event dispatch loop
    before running the strategy.

.. literalinclude:: ../samples/tutorial_twitter_bitstamp.py

The output should look like this:

.. literalinclude:: ../samples/tutorial_twitter_bitstamp.output
