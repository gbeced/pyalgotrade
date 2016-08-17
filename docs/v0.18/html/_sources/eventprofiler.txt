Event profiler
==============

Inspired in QSTK (http://wiki.quantsoftware.org/index.php?title=QSTK_Tutorial_9), the **eventprofiler** module is a tool to analyze,
statistically, how events affect future equity prices.
The event profiler scans over historical data for a specified event and then calculates the impact of that event on the equity prices in the past
and the future over a certain lookback period.

**The goal of this tool is to help you quickly validate an idea, before moving forward with the backtesting process.**

.. automodule:: pyalgotrade.eventprofiler
    :members:
    :member-order: bysource
    :show-inheritance:

Example
-------

The following example is inspired on the 'Buy-on-Gap Model' from Ernie Chan's book:
'Algorithmic Trading: Winning Strategies and Their Rationale':

 * The idea is to select a stock near the market open whose returns from their previous day's lows
   to today's open are lower that one standard deviation. The standard deviation is computed using
   the daily close-to-close returns of the last 90 days. These are the stocks that "gapped down".
 * This is narrowed down by requiring the open price to be higher than the 20-day moving average
   of the closing price.

.. literalinclude:: ../samples/eventstudy.py

The code is doing 4 things:

 1. Declaring a :class:`Predicate` that implements the 'Buy-on-Gap Model' event identification.
 2. Loading bars for some stocks.
 3. Running the analysis.
 4. Plotting the results.

This is what the output should look like:

.. image:: ../samples/eventstudy.png

.. literalinclude:: ../samples/eventstudy.output

Note that **Cummulative returns are normalized to the time of the event**.
