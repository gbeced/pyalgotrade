strategy -- Basic strategy classes
==================================

Strategies are the classes that you define that implement the trading logic, when to buy, when to sell, etc.
Buying and selling can be done in 3 different ways:

    * Using a simple interface to place market orders:
        * :meth:`pyalgotrade.strategy.BaseStrategy.order`
    * Using a long/short position based interface:
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterLong`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterShort`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterLongLimit`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterShortLimit`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterLongStop`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterShortStop`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterLongStopLimit`
        * :meth:`pyalgotrade.strategy.BaseStrategy.enterShortStopLimit`
    * Using the :class:`pyalgotrade.broker.Broker` interface directly.

Strategy
--------

.. automodule:: pyalgotrade.strategy
    :members: BaseStrategy, BacktestingStrategy
    :show-inheritance:

Position
--------

.. automodule:: pyalgotrade.strategy.position
    :members: Position
    :show-inheritance:

