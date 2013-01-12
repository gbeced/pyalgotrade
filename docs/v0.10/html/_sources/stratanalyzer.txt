stratanalyzer -- Strategy analyzers
===================================

Strategy analyzers provide an extensible way to attach different calculations to strategy executions.

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer

Returns
-------
.. automodule:: pyalgotrade.stratanalyzer.returns
    :members: Returns

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
    :member-order: bysource

Example
-------
This example depends on smacross_strategy.py from the tutorial section.

.. literalinclude:: ../samples/sample-strategy-analyzer.py

The output should look like this:

.. literalinclude:: ../samples/sample-strategy-analyzer.output
