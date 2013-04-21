strategy -- Basic strategy classes
==================================

Strategies are the classes that you define, that implement a certain trading strategy. When to buy, when to sell, etc.
Buying and selling can be done in 3 different ways:

    * Using a simple interface to place market orders:
        * :meth:`pyalgotrade.strategy.Strategy.order`
    * Using a long/short position based interface:
        * :meth:`pyalgotrade.strategy.Strategy.enterLong`
        * :meth:`pyalgotrade.strategy.Strategy.enterShort`
        * :meth:`pyalgotrade.strategy.Strategy.enterLongLimit`
        * :meth:`pyalgotrade.strategy.Strategy.enterShortLimit`
        * :meth:`pyalgotrade.strategy.Strategy.enterLongStop`
        * :meth:`pyalgotrade.strategy.Strategy.enterShortStop`
        * :meth:`pyalgotrade.strategy.Strategy.enterLongStopLimit`
        * :meth:`pyalgotrade.strategy.Strategy.enterShortStopLimit`
        * :meth:`pyalgotrade.strategy.Strategy.exitPosition`
    * Using the :class:`pyalgotrade.broker.Broker` interface directly.

.. automodule:: pyalgotrade.strategy
    :members: Strategy

.. automodule:: pyalgotrade.strategy.position
    :members: Position


