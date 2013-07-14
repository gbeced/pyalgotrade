stratanalyzer -- Strategy analyzers
===================================

Strategy analyzers provide an extensible way to attach different calculations to strategy executions.

.. automodule:: pyalgotrade.stratanalyzer
    :members: StrategyAnalyzer
    :show-inheritance:

Returns
-------
.. automodule:: pyalgotrade.stratanalyzer.returns
    :members: Returns
    :show-inheritance:

Sharpe Ratio
------------
.. automodule:: pyalgotrade.stratanalyzer.sharpe
    :members: SharpeRatio
    :show-inheritance:

DrawDown
--------
.. automodule:: pyalgotrade.stratanalyzer.drawdown
    :members: DrawDown
    :show-inheritance:

Trades
------
.. automodule:: pyalgotrade.stratanalyzer.trades
    :members: Trades
    :member-order: bysource
    :show-inheritance:

Example
-------
This example depends on smacross_strategy.py from the tutorial section.

.. literalinclude:: ../samples/sample-strategy-analyzer.py

The output should look like this:

.. literalinclude:: ../samples/sample-strategy-analyzer.output
