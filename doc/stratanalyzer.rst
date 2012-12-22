stratanalyzer -- Strategy analyzers
===================================

Strategy analyzers provide an extensible way to attach different calculations to strategy executions.

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer

Returns
-------
.. automodule:: pyalgotrade.stratanalyzer.returns
    :members: Returns, ReturnsDataSeries, CumulativeReturnsDataSeries

Sharpe Ratio
------------
.. automodule:: pyalgotrade.stratanalyzer.sharpe
    :members: SharpeRatio

DrawDown
--------
.. automodule:: pyalgotrade.stratanalyzer.drawdown
    :members: DrawDown

Trades
------
.. automodule:: pyalgotrade.stratanalyzer.trades
    :members: Trades

Example
-------
This example depends on smacross_strategy.py from the tutorial section.

.. literalinclude:: ../samples/sample-strategy-analyzer.py

The output should look like this: ::

    Final portfolio value: $1124.90
    Cumulative returns: 12.49 %
    Sharpe ratio: 0.39
    Max. drawdown: 17.85 %
    Max. drawdown duration: 193 days
    Winning trades: 3
    Winning avg: $101
    Losing trades: 8
    Losing avg: $-26

