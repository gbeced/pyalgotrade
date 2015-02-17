.. _bitstamp-tutorial-label:

Bitstamp Example
================

This goal of this simple SMA crossover example is to show how to put all the pieces together to paper
trade a strategy using realtime feeds supplied by Bitstamp (https://www.bitstamp.net/).

This example assumes that you're already familiar with the basic concepts presented
in the :ref:`tutorial-label` section.

The key things to highlight are:

 1. We're using :class:`pyalgotrade.strategy.BaseStrategy` instead of :class:`pyalgotrade.strategy.BacktestingStrategy`
    as the base class. This is not a backtest.
 2. Trade events get notified via the call to **onBars**. No need to manually subscribe.
 3. Order book update events are handled by manually subscribing to :class:`pyalgotrade.bitstamp.barfeed.LiveTradeFeed.getOrderBookUpdateEvent`.
    This is needed to be up to date with latest bid and ask prices.

.. literalinclude:: ../samples/tutorial_bitstamp_1.py

The output should look like this: ::

    2014-03-15 00:35:59,085 bitstamp [INFO] Initializing websocket client.
    2014-03-15 00:35:59,452 bitstamp [INFO] Connection established.
    2014-03-15 00:35:59,453 bitstamp [INFO] Initialization ok.
    2014-03-15 00:36:30,726 strategy [INFO] Order book updated. Best bid: 629.6. Best ask: 630.0
    2014-03-15 00:39:04,829 strategy [INFO] Order book updated. Best bid: 628.89. Best ask: 630.0
    2014-03-15 00:44:18,845 strategy [INFO] Price: 630.0. Volume: 0.01.
    2014-03-15 00:44:18,894 strategy [INFO] Order book updated. Best bid: 630.0. Best ask: 631.49
    2014-03-15 00:44:29,719 strategy [INFO] Price: 630.0. Volume: 0.02.
    2014-03-15 00:44:59,861 strategy [INFO] Price: 631.49. Volume: 0.03360823.
    2014-03-15 00:45:37,425 strategy [INFO] Order book updated. Best bid: 630.0. Best ask: 631.6
    2014-03-15 00:45:39,848 strategy [INFO] Price: 631.6. Volume: 3.35089782.
    2014-03-15 00:45:39,918 strategy [INFO] Price: 632.24. Volume: 0.136.
    2014-03-15 00:45:39,971 strategy [INFO] Price: 632.24. Volume: 0.138.
    2014-03-15 00:45:40,057 strategy [INFO] Price: 632.25. Volume: 0.09076537.
    2014-03-15 00:45:40,104 strategy [INFO] Price: 632.42. Volume: 0.74011681.
    2014-03-15 00:45:40,205 strategy [INFO] Order book updated. Best bid: 630.0. Best ask: 632.42
    2014-03-15 00:48:30,005 strategy [INFO] Price: 630.0. Volume: 4.97.
    2014-03-15 00:48:30,039 strategy [INFO] Price: 629.6. Volume: 0.09.
    2014-03-15 00:48:30,121 strategy [INFO] Price: 629.54. Volume: 0.09.
    .
    .
    .
    2014-03-15 00:48:33,053 strategy [INFO] Price: 625.55. Volume: 1.296299.
    2014-03-15 00:48:33,164 strategy [INFO] Price: 625.52. Volume: 0.0924981.
    2014-03-15 00:48:33,588 strategy [INFO] Price: 625.45. Volume: 13.46260589.
    2014-03-15 00:48:33,635 strategy [INFO] Order book updated. Best bid: 629.26. Best ask: 632.42
    2014-03-15 00:48:33,727 strategy [INFO] Price: 625.45. Volume: 1.75.
    2014-03-15 00:48:34,261 strategy [INFO] Price: 625.48. Volume: 0.1.
    2014-03-15 00:48:34,908 strategy [INFO] Order book updated. Best bid: 629.26. Best ask: 631.39
    2014-03-15 00:48:36,203 strategy [INFO] Order book updated. Best bid: 629.26. Best ask: 632.42
    .
    .
    .
    2014-03-15 00:49:01,945 strategy [INFO] Order book updated. Best bid: 629.26. Best ask: 631.39
    2014-03-15 00:49:34,743 strategy [INFO] Order book updated. Best bid: 629.26. Best ask: 631.28
    2014-03-15 00:49:57,651 strategy [INFO] Price: 629.26. Volume: 0.66893865.
    2014-03-15 00:49:57,651 strategy [INFO] Entry signal. Buy at 631.28
    2014-03-15 00:50:09,934 strategy [INFO] Order book updated. Best bid: 629.26. Best ask: 631.39
    2014-03-15 00:50:20,786 strategy [INFO] Order book updated. Best bid: 627.02. Best ask: 631.39
    2014-03-15 00:50:25,658 strategy [INFO] Price: 631.39. Volume: 0.01.
    2014-03-15 00:50:25,732 strategy [INFO] Price: 631.39. Volume: 0.01.
    2014-03-15 00:50:25,791 strategy [INFO] Price: 631.93. Volume: 0.5.
    2014-03-15 00:50:25,847 strategy [INFO] Price: 632.42. Volume: 0.25988319.
    2014-03-15 00:50:25,900 strategy [INFO] Price: 632.42. Volume: 0.184.
    2014-03-15 00:50:25,952 strategy [INFO] Price: 632.42. Volume: 0.184.
    2014-03-15 00:50:26,000 strategy [INFO] Price: 632.42. Volume: 0.184.
    2014-03-15 00:50:26,065 strategy [INFO] Price: 632.44. Volume: 0.184.
    2014-03-15 00:50:26,139 strategy [INFO] Price: 632.97. Volume: 0.092.
    2014-03-15 00:50:26,300 strategy [INFO] Order book updated. Best bid: 627.02. Best ask: 629.0
    2014-03-15 00:50:26,398 strategy [INFO] Price: 633.1. Volume: 0.16211681.
    2014-03-15 00:50:29,850 strategy [INFO] Position opened at 629.0
    2014-03-15 00:50:29,850 strategy [INFO] Price: 629.0. Volume: 0.25152623.
    2014-03-15 00:50:29,850 strategy [INFO] Exit signal. Sell at 627.02
    2014-03-15 00:50:37,294 strategy [INFO] Order book updated. Best bid: 627.02. Best ask: 633.1
    2014-03-15 00:50:43,526 strategy [INFO] Order book updated. Best bid: 627.02. Best ask: 633.08
    2014-03-15 00:51:07,604 strategy [INFO] Order book updated. Best bid: 627.02. Best ask: 632.99
    2014-03-15 00:51:46,194 strategy [INFO] Order book updated. Best bid: 627.02. Best ask: 630.89
    2014-03-15 00:52:08,223 strategy [INFO] Position closed at 627.02
    2014-03-15 00:52:08,223 strategy [INFO] Price: 627.02. Volume: 0.0924979.
    2014-03-15 00:52:08,290 strategy [INFO] Price: 627.02. Volume: 0.02.
    2014-03-15 00:52:08,530 strategy [INFO] Order book updated. Best bid: 627.01. Best ask: 627.02
    2014-03-15 00:52:35,347 strategy [INFO] Price: 630.89. Volume: 0.07.
    2014-03-15 00:52:35,347 strategy [INFO] Entry signal. Buy at 627.02
    2014-03-15 00:52:35,348 strategy [INFO] Price: 630.95. Volume: 0.09.
    2014-03-15 00:52:35,428 strategy [INFO] Price: 631.0. Volume: 0.05.
    .
    .
    .
    2014-03-15 00:54:14,077 strategy [INFO] Order book updated. Best bid: 628.81. Best ask: 632.4
    2014-03-15 00:54:21,084 strategy [INFO] Order book updated. Best bid: 631.0. Best ask: 632.4
    2014-03-15 00:54:34,484 strategy [INFO] Price: 632.4. Volume: 0.296299.
    2014-03-15 00:54:34,484 strategy [INFO] Exit signal. Sell at 631.0
    2014-03-15 00:54:34,484 strategy [INFO] Position entry canceled
    2014-03-15 00:54:34,578 strategy [INFO] Price: 632.45. Volume: 3.5.
    2014-03-15 00:54:34,642 strategy [INFO] Price: 632.45. Volume: 0.5715.
    2014-03-15 00:54:34,708 strategy [INFO] Price: 632.46. Volume: 0.136.
    2014-03-15 00:54:34,789 strategy [INFO] Price: 632.46. Volume: 1.2682.
    2014-03-15 00:54:34,885 strategy [INFO] Price: 632.46. Volume: 3.5.
    2014-03-15 00:54:34,949 strategy [INFO] Price: 632.46. Volume: 5.25.
    2014-03-15 00:54:35,029 strategy [INFO] Price: 632.47. Volume: 9.88740834.
    2014-03-15 00:54:35,165 strategy [INFO] Price: 632.89. Volume: 18.24259574.
    2014-03-15 00:54:35,165 strategy [INFO] Entry signal. Buy at 632.4
    2014-03-15 00:54:35,286 strategy [INFO] Price: 633.0. Volume: 0.092.
    2014-03-15 00:54:35,357 strategy [INFO] Price: 633.1. Volume: 0.37612853.
    .
    .
    .
    2014-03-15 00:56:48,885 strategy [INFO] Order book updated. Best bid: 632.1. Best ask: 634.35
    2014-03-15 00:56:57,234 strategy [INFO] Position opened at 632.1
    2014-03-15 00:56:57,235 strategy [INFO] Price: 632.1. Volume: 0.66267992.
    2014-03-15 00:56:57,235 strategy [INFO] Exit signal. Sell at 632.1
    2014-03-15 00:56:57,268 strategy [INFO] Price: 631.83. Volume: 59.33732008.
    2014-03-15 00:56:57,356 strategy [INFO] Order book updated. Best bid: 631.83. Best ask: 634.35
    2014-03-15 00:57:03,528 strategy [INFO] Price: 631.83. Volume: 0.08267992.
    2014-03-15 00:57:03,604 strategy [INFO] Order book updated. Best bid: 631.0. Best ask: 631.83
    2014-03-15 00:57:04,824 strategy [INFO] Order book updated. Best bid: 631.0. Best ask: 634.34
    2014-03-15 00:57:09,775 strategy [INFO] Order book updated. Best bid: 631.0. Best ask: 634.33
    2014-03-15 00:57:11,112 strategy [INFO] Order book updated. Best bid: 632.1. Best ask: 634.33
    2014-03-15 00:57:15,822 strategy [INFO] Position closed at 632.1
    2014-03-15 00:57:15,822 strategy [INFO] Price: 632.1. Volume: 0.2.
    2014-03-15 00:57:20,839 strategy [INFO] Price: 632.1. Volume: 0.46267992.
    2014-03-15 00:57:22,065 strategy [INFO] Price: 631.2. Volume: 0.03732008.
    2014-03-15 00:57:22,122 strategy [INFO] Price: 634.33. Volume: 0.135.
    2014-03-15 00:57:22,122 strategy [INFO] Entry signal. Buy at 634.33
    2014-03-15 00:57:22,184 strategy [INFO] Price: 634.34. Volume: 0.97972409.
    .
    .
    .

In order to live trade this strategy you should use :class:`pyalgotrade.bitstamp.broker.LiveBroker` instead of
:class:`pyalgotrade.bitstamp.broker.PaperTradingBroker`.

**Note that if you try to live trade this strategy you will probably loose money.**
Before jumping to live trading, be sure to write your own strategy, backtest and paper trade it thoroughly
before risking real money.
