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

Brokers
    Brokers are responsible for executing orders.

DataSeries
    A data series is an abstraction used to manage historical data.

Technicals
    These are a set of filters that you use to make calculations on top of DataSeries.
    For example SMA (Simple Moving Average), RSI (Relative Strength Index), etc. These filters are modeled as DataSeries decorators.

Optimizer
    These are a set of classes that allow you to distribute backtesting among different computers,
    or different processes running in the same computer, or a combination of both. They make horizontal scaling easy.

Having said all that, the first thing that we'll need to test our strategies is some data.
Let's use Oracle's stock prices for year 2000, which we'll download with the following command: ::

    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('orcl', 2000, 'orcl-2000.csv')"

The pyalgotrade.tools.yahoofinance package downloads CSV formatted data from Yahoo! Finance. 
The orcl-2000.csv file should look like this: ::

    Date,Open,High,Low,Close,Volume,Adj Close
    2000-12-29,30.87,31.31,28.69,29.06,31655500,28.35
    2000-12-28,30.56,31.12,30.37,31.06,25055600,30.30
    2000-12-27,30.37,31.06,29.37,30.69,26441700,29.94
    .
    .
    2000-01-04,115.50,118.62,105.00,107.69,116850000,26.26
    2000-01-03,124.62,125.19,111.62,118.12,98122000,28.81

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

One important thing about technicals is that they can be stacked. That is because they're modeled as data series as well.
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
 * If a long order is in place, and the adjusted close price drops below the SMA(15) we exit the long position (we place a sell market order).

.. literalinclude:: ../samples/tutorial-4.py

If you run the script you should see something like this: 

.. literalinclude:: ../samples/tutorial-4.output

But what if we used 30 as the SMA period instead of 15 ? Would that yield better results or worse ?
We could certainly do something like this:

::

    for i in range(10, 30):
        run_strategy(i)

and we would find out that we can get better results with a SMA(20): ::

    Final portfolio value: $1075.38

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

To illustrate this we'll use a strategy known as RSI2 (http://stockcharts.com/school/doku.php?id=chart_school:trading_strategies:rsi2)
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

Let's start by downloading 3 years of daily bars for 'Dow Jones Industrial Average': ::

    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('dia', 2009, 'dia-2009.csv')"
    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('dia', 2010, 'dia-2010.csv')" 
    python -c "from pyalgotrade.tools import yahoofinance; yahoofinance.download_daily_bars('dia', 2011, 'dia-2011.csv')"

This is the server script:

.. literalinclude:: ../samples/tutorial-optimizer-server.py

The server code is doing 3 things:

 1. Declaring a generator function that builds parameters.
 2. Loading the feed with the CSV files we downloaded.
 3. Running the server that will wait for incoming connections on port 5000.

This is the worker script:

.. literalinclude:: ../samples/tutorial-optimizer-worker.py

The worker code is doing 2 things:

 1. Declaring the RSI2 strategy.
 2. Using pyalgotrade.optimizer.worker module to run the strategy in parallel with the data supplied by the server.


When you run the server and the client/s you'll see something like this on the server console: ::

    INFO 2012-03-24 22:29:29,860: Loading bars
    INFO 2012-03-24 22:29:30,053: Waiting for workers
    INFO 2012-03-24 22:29:33,640: Partial result $2036.90 with parameters: (150, 5, 2, 75, 5)
    INFO 2012-03-24 22:29:33,769: Partial result $2089.20 with parameters: (150, 5, 2, 76, 5)
    INFO 2012-03-24 22:29:33,896: Partial result $2100.40 with parameters: (150, 5, 2, 77, 5)
    INFO 2012-03-24 22:29:34,025: Partial result $2100.40 with parameters: (150, 5, 2, 78, 5)
    INFO 2012-03-24 22:29:34,153: Partial result $2100.40 with parameters: (150, 5, 2, 79, 5)
    INFO 2012-03-24 22:29:34,280: Partial result $2112.20 with parameters: (150, 5, 2, 80, 5)
    .
    .

and something like this on the worker/s console: ::

    INFO 2012-03-24 22:29:33,515: Running strategy with parameters (150, 5, 2, 75, 5)
    INFO 2012-03-24 22:29:33,638: Result 2036.9
    INFO 2012-03-24 22:29:33,643: Running strategy with parameters (150, 5, 2, 76, 5)
    INFO 2012-03-24 22:29:33,767: Result 2089.2
    INFO 2012-03-24 22:29:33,772: Running strategy with parameters (150, 5, 2, 77, 5)
    INFO 2012-03-24 22:29:33,895: Result 2100.4
    INFO 2012-03-24 22:29:33,899: Running strategy with parameters (150, 5, 2, 78, 5)
    INFO 2012-03-24 22:29:34,023: Result 2100.4
    INFO 2012-03-24 22:29:34,028: Running strategy with parameters (150, 5, 2, 79, 5)
    INFO 2012-03-24 22:29:34,151: Result 2100.4
    INFO 2012-03-24 22:29:34,156: Running strategy with parameters (150, 5, 2, 80, 5)
    INFO 2012-03-24 22:29:34,278: Result 2112.2
    .
    .

Note that you should run **only one server and one or more workers**.

If you just want to run strategies in parallel in your own desktop you can take advantage of the pyalgotrade.optimizer.local
module like this:

.. literalinclude:: ../samples/tutorial-optimizer-local.py

The code is doing 4 things:

 1. Declaring the RSI2 strategy.
 2. Declaring a generator function that builds parameters.
 3. Loading the feed with the CSV files we downloaded.
 4. Using the pyalgotrade.optimizer.local module to run the strategy in parallel and find the best result.

When you run this code you should see something like this: ::

    INFO 2012-03-25 00:07:34,793: Loading bars
    INFO 2012-03-25 00:07:34,996: Waiting for workers
    INFO 2012-03-25 00:07:35,366: Partial result $2036.90 with parameters: (150, 5, 2, 75, 5)
    INFO 2012-03-25 00:07:35,385: Partial result $2089.20 with parameters: (150, 5, 2, 76, 5)
    INFO 2012-03-25 00:07:35,499: Partial result $2100.40 with parameters: (150, 5, 2, 77, 5)
    INFO 2012-03-25 00:07:35,515: Partial result $2100.40 with parameters: (150, 5, 2, 78, 5)
    INFO 2012-03-25 00:07:35,632: Partial result $2100.40 with parameters: (150, 5, 2, 79, 5)
    INFO 2012-03-25 00:07:35,646: Partial result $2112.20 with parameters: (150, 5, 2, 80, 5)
    INFO 2012-03-25 00:07:35,763: Partial result $2115.50 with parameters: (150, 5, 2, 81, 5)
    INFO 2012-03-25 00:07:35,775: Partial result $2076.60 with parameters: (150, 5, 2, 82, 5)
    INFO 2012-03-25 00:07:35,895: Partial result $2003.60 with parameters: (150, 5, 2, 83, 5)
    INFO 2012-03-25 00:07:35,902: Partial result $2003.60 with parameters: (150, 5, 2, 84, 5)
    INFO 2012-03-25 00:07:36,026: Partial result $2003.60 with parameters: (150, 5, 2, 85, 5)
    INFO 2012-03-25 00:07:36,033: Partial result $2048.60 with parameters: (150, 5, 2, 86, 5)
    INFO 2012-03-25 00:07:36,157: Partial result $2061.70 with parameters: (150, 5, 2, 87, 5)
    INFO 2012-03-25 00:07:36,163: Partial result $2075.00 with parameters: (150, 5, 2, 88, 5)
    INFO 2012-03-25 00:07:36,288: Partial result $2082.00 with parameters: (150, 5, 2, 89, 5)
    INFO 2012-03-25 00:07:36,293: Partial result $2080.70 with parameters: (150, 5, 2, 90, 5)
    INFO 2012-03-25 00:07:36,418: Partial result $2086.80 with parameters: (150, 5, 2, 91, 5)
    INFO 2012-03-25 00:07:36,424: Partial result $2086.80 with parameters: (150, 5, 2, 92, 5)
    .
    .

For the record, the best result found was $2314.40 with the following parameters:
 1. entrySMA: 154
 2. exitSMA: 5
 3. rsiPeriod: 2
 4. overBoughtThreshold: 91
 5. overSoldThreshold: 18


If you don't have access to a cluster of computers, then you can take advantage of :doc:`googleappengine`.

Plotting
--------

PyAlgoTrade makes it very easy to plot a strategy execution.
Save this SMA crossover strategy as smacross_strategy.py:

.. literalinclude:: ../samples/smacross_strategy.py

and save this code to a different file:

.. literalinclude:: ../samples/tutorial-5.py

The code is doing 3 things:

 1. Loading the feed from a CSV file.
 2. Running the strategy with the bars supplied by the feed and a StrategyPlotter attached.
 3. Plotting the strategy.

This is what the plot looks like:

.. image:: ../samples/tutorial-5.png

I hope you enjoyed this quick introduction. I'd recommend you to download PyAlgoTrade here: http://gbeced.github.com/pyalgotrade/downloads/index.html
and get started writing you own strategies.

