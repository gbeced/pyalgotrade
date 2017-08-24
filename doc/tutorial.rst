.. _tutorial-label:

Tutorial
========

The goal of this tutorial is to give you a quick introduction to PyAlgoTrade.
As described in the introduction, the goal of PyAlgoTrade is to help you backtest stock trading strategies.
Let's say you have an idea for a trading strategy and you'd like to evaluate it with historical data and see how it behaves,
then PyAlgoTrade should allow you to do so with minimal effort.

Before I move on I would like to thank Pablo Jorge who helped reviewing the initial design and documentation.

**This tutorial was developed on a UNIX environment, but the steps to adapt it to a Windows environment should be straightforward.**

PyAlgoTrade has 6 main components:

 * Strategies
 * Feeds
 * Brokers
 * DataSeries
 * Technicals
 * Optimizer

Strategies
    These are the classes that you define that implement the trading logic. When to buy, when to sell, etc.

Feeds
    These are data providing abstractions. For example, you'll use a CSV feed that loads bars from a CSV
    (Comma-separated values) formatted file to feed data to a strategy.
    Feeds are not limited to bars. For example, there is a Twitter feed that allows incorporating Twitter
    events into trading decisions.

Brokers
    Brokers are responsible for executing orders.

DataSeries
    A data series is an abstraction used to manage time series data.

Technicals
    These are a set of filters that you use to make calculations on top of DataSeries.
    For example SMA (Simple Moving Average), RSI (Relative Strength Index), etc. These filters are modeled as DataSeries decorators.

Optimizer
    These are a set of classes that allow you to distribute backtesting among different computers,
    or different processes running in the same computer, or a combination of both. They make horizontal scaling easy.

Having said all that, the first thing that we'll need to test our strategies is some data.
Let's use Oracle's stock prices for year 2000, which we'll download with the following command: ::

    python -m "pyalgotrade.tools.quandl" --source-code="WIKI" --table-code="ORCL" --from-year=2000 --to-year=2000 --storage=. --force-download --frequency=daily

The pyalgotrade.tools.quandl tool downloads CSV formatted data from `Quandl <https://www.quandl.com/>`_. 
The first few lines of ``WIKI-ORCL-2000-quandl.csv`` should look like this: ::

    Date,Open,High,Low,Close,Volume,Ex-Dividend,Split Ratio,Adj. Open,Adj. High,Adj. Low,Adj. Close,Adj. Volume
    2000-12-29,30.88,31.31,28.69,29.06,31702200.0,0.0,1.0,28.121945213877797,28.513539658242028,26.127545601883227,26.46449896098733,31702200.0
    2000-12-28,30.56,31.63,30.38,31.06,25053600.0,0.0,1.0,27.830526092490462,28.804958779629363,27.666602836710087,28.285868469658173,25053600.0
    2000-12-27,30.38,31.06,29.38,30.69,26437500.0,0.0,1.0,27.666602836710087,28.285868469658173,26.755918082374667,27.94891511055407,26437500.0
    2000-12-26,31.5,32.19,30.0,30.94,20589500.0,0.0,1.0,28.68656976156576,29.3149422420572,27.32054263006263,28.176586299137927,20589500.0
    2000-12-22,30.38,31.98,30.0,31.88,35568200.0,0.0,1.0,27.666602836710087,29.123698443646763,27.32054263006263,29.032629968213218,35568200.0
    2000-12-21,27.81,30.25,27.31,29.5,46719700.0,0.0,1.0,25.326143018068056,27.548213818646484,24.870800640900345,26.86520025289492,46719700.0
    2000-12-20,28.06,29.81,27.5,28.5,54440500.0,0.0,1.0,25.55381420665191,27.147512526738897,25.043830744224078,25.9545154985595,54440500.0
    2000-12-19,31.81,33.13,30.13,30.63,58653700.0,0.0,1.0,28.968882035409738,30.170985911132497,27.438931648126232,27.894274025293942,58653700.0
    2000-12-18,30.0,32.44,29.94,32.0,61640100.0,0.0,1.0,27.32054263006263,29.542613430641055,27.265901544802503,29.14191213873347,61640100.0

Let's start with a simple strategy, that is, one that just prints closing prices as they are processed:

.. literalinclude:: ../samples/tutorial-1.py

The code is doing 3 main things:
 1. Declaring a new strategy. There is only one method that has to be defined, *onBars*, which is called for every bar in the feed.
 2. Loading the feed from a CSV file.
 3. Running the strategy with the bars supplied by the feed.

If you run the script you should see the closing prices in order:

.. literalinclude:: ../samples/tutorial-1.output

Let's move on with a strategy that prints closing SMA prices, to illustrate how technicals are used:

.. literalinclude:: ../samples/tutorial-2.py

This is very similar to the previous example, except that:

 1. We're initializing an SMA filter over the closing price data series.
 2. We're printing the current SMA value along with the closing price.

If you run the script you should see the closing prices and the corresponding SMA values, but in this case the first 14 SMA values are None.
That is because we need at least 15 values to get something out of the SMA:

.. literalinclude:: ../samples/tutorial-2.output

All the technicals will return None when the value can't be calculated at a given time.

One important thing about technicals is that they can be combined. That is because they're modeled as DataSeries as well.
For example, getting an SMA over the RSI over the closing prices is as simple as this:

.. literalinclude:: ../samples/tutorial-3.py

If you run the script you should see a bunch of values on the screen where:

 * The first 14 RSI values are None. That is because we need at least 15 values to get an RSI value.
 * The first 28 SMA values are None. That is because the first 14 RSI values are None, and the 15th one is the first not None value that the SMA filter receives.
   We can calculate the SMA(15) only when we have 15 not None values .

.. literalinclude:: ../samples/tutorial-3.output

Trading
-------

Let's move on with a simple strategy, this time simulating actual trading. The idea is very simple:

 * If the adjusted close price is above the SMA(15) we enter a long position (we place a buy market order).
 * If a long position is in place, and the adjusted close price drops below the SMA(15) we exit the long position (we place a sell market order).

.. literalinclude:: ../samples/tutorial-4.py

If you run the script you should see something like this: 

.. literalinclude:: ../samples/tutorial-4.output

But what if we used 30 as the SMA period instead of 15 ? Would that yield better results or worse ?
We could certainly do something like this:

::

    for i in range(10, 30):
        run_strategy(i)

and we would find out that we can get better results with a SMA(20): ::

    Final portfolio value: $1071.03

This is ok if we only have to try a limited set of parameters values. But if we have to test a strategy with multiple
parameters, then the serial approach is definitely not going to scale as strategies get more complex.

Optimizing
----------

Meet the optimizer component. The idea is very simple:

 * There is one server responsible for:
    * Providing the bars to run the strategy.
    * Providing the parameters to run the strategy.
    * Recording the strategy results from each of the workers.
 * There are multiple workers responsible for:
    * Running the strategy with the bars and parameters provided by the server.

To illustrate this we'll use a strategy known as `RSI2 <http://stockcharts.com/school/doku.php?id=chart_school:trading_strategies:rsi2>`_
which requires the following parameters:

 * An SMA period for trend identification. We'll call this entrySMA and will range between 150 and 250.
 * A smaller SMA period for the exit point. We'll call this exitSMA and will range between 5 and 15.
 * An RSI period for entering both short/long positions. We'll call this rsiPeriod and will range between 2 and 10.
 * An RSI oversold threshold for long position entry. We'll call this overSoldThreshold and will range between 5 and 25.
 * An RSI overbought threshold for short position entry. We'll call this overBoughtThreshold and will range between 75 and 95.

If my math is ok, those are 4409559 different combinations.

Testing this strategy for one set of parameters took me about 0.16 seconds. If I execute all the combinations serially
it'll take me about 8.5 days to evaluate all of them and find the best set of parameters. That is a long time, but
if I can get ten 8-core computers to do the job then the total time will go down to about 2.5 hours.

Long story short, **we need to go parallel**.

Let's start by downloading 3 years of daily bars for 'IBM': ::

    python -m "pyalgotrade.tools.quandl" --source-code="WIKI" --table-code="IBM" --from-year=2009 --to-year=2011 --storage=. --force-download --frequency=daily

Save this code as rsi2.py:

.. literalinclude:: ../samples/rsi2.py

This is the server script:

.. literalinclude:: ../samples/tutorial-optimizer-server.py

The server code is doing 3 things:

 1. Declaring a generator function that yields different parameter combinations for the strategy.
 2. Loading the feed with the CSV files we downloaded.
 3. Running the server that will wait for incoming connections on port 5000.

This is the worker script that uses the **pyalgotrade.optimizer.worker** module to run the strategy in parallel with
the data supplied by the server:

.. literalinclude:: ../samples/tutorial-optimizer-worker.py

When you run the server and the client/s you'll see something like this on the server console: ::

    2017-07-21 22:56:51,944 pyalgotrade.optimizer.server [INFO] Starting server
    2017-07-21 22:56:51,944 pyalgotrade.optimizer.xmlrpcserver [INFO] Loading bars
    2017-07-21 22:56:52,609 pyalgotrade.optimizer.xmlrpcserver [INFO] Started serving
    2017-07-21 22:58:50,073 pyalgotrade.optimizer.xmlrpcserver [INFO] Best result so far 1261295.07089 with parameters ('ibm', 150, 5, 2, 83, 24)
    .
    .

and something like this on the worker/s console: ::

    2017-07-21 22:56:57,884 localworker [INFO] Started running
    2017-07-21 22:56:57,884 localworker [INFO] Started running
    2017-07-21 22:56:58,439 localworker [INFO] Running strategy with parameters ('ibm', 150, 5, 2, 84, 15)
    2017-07-21 22:56:58,498 localworker [INFO] Running strategy with parameters ('ibm', 150, 5, 2, 94, 5)
    2017-07-21 22:56:58,918 localworker [INFO] Result 1137855.88871
    2017-07-21 22:56:58,918 localworker [INFO] Running strategy with parameters ('ibm', 150, 5, 2, 84, 14)
    2017-07-21 22:56:58,996 localworker [INFO] Result 1027761.85581
    2017-07-21 22:56:58,997 localworker [INFO] Running strategy with parameters ('ibm', 150, 5, 2, 93, 25)
    2017-07-21 22:56:59,427 localworker [INFO] Result 1092194.67448
    2017-07-21 22:57:00,016 localworker [INFO] Result 1260766.64479
    .
    .

Note that you should run **only one server and one or more workers**.

If you just want to run strategies in parallel in your own desktop you can take advantage of the **pyalgotrade.optimizer.local**
module like this:

.. literalinclude:: ../samples/tutorial-optimizer-local.py

The code is doing 3 things:

 1. Declaring a generator function that yields different parameter combinations.
 2. Loading the feed with the CSV files we downloaded.
 3. Using the **pyalgotrade.optimizer.local** module to run the strategy in parallel and find the best result.

When you run this code you should see something like this: ::

    2017-07-21 22:59:26,921 pyalgotrade.optimizer.local [INFO] Starting server
    2017-07-21 22:59:26,922 pyalgotrade.optimizer.xmlrpcserver [INFO] Loading bars
    2017-07-21 22:59:26,922 pyalgotrade.optimizer.local [INFO] Starting workers
    2017-07-21 22:59:27,642 pyalgotrade.optimizer.xmlrpcserver [INFO] Started serving
    2017-07-21 23:01:14,306 pyalgotrade.optimizer.xmlrpcserver [INFO] Best result so far 1261295.07089 with parameters ('ibm', 150, 5, 2, 83, 24)
    .
    .


Plotting
--------

PyAlgoTrade makes it very easy to plot a strategy execution.

Save this as sma_crossover.py:

.. literalinclude:: ../samples/sma_crossover.py

and save this code to a different file:

.. literalinclude:: ../samples/tutorial-5.py

The code is doing 3 things:

 1. Loading the feed from a CSV file.
 2. Running the strategy with the bars supplied by the feed and a StrategyPlotter attached.
 3. Plotting the strategy.

This is what the plot looks like:

.. image:: ../samples/tutorial-5.png

I hope you enjoyed this quick introduction. I'd recommend you to download PyAlgoTrade here: http://gbeced.github.io/pyalgotrade/downloads/index.html 
and get started writing you own strategies.

You can also find more examples in the :ref:`samples-label` section.
