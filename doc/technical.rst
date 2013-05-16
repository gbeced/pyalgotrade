technical -- Technical indicators
=================================

.. automodule:: pyalgotrade.technical
    :members: EventWindow, EventBasedFilter

Example
-------

The following example shows how to combine an :class:`EventWindow` and an :class:`EventBasedFilter` to build a custom filter:

.. literalinclude:: ../samples/technical-1.py

The output should be:

.. literalinclude:: ../samples/technical-1.output

Moving Averages
---------------

.. automodule:: pyalgotrade.technical.ma
    :members: SMA, EMA, WMA

.. automodule:: pyalgotrade.technical.vwap
    :members: VWAP

Momentum Indicators
-------------------

.. automodule:: pyalgotrade.technical.rsi
    :members: RSI

.. automodule:: pyalgotrade.technical.stoch
    :members: StochasticOscillator

.. automodule:: pyalgotrade.technical.roc
    :members: RateOfChange

Other Indicators
----------------

.. automodule:: pyalgotrade.technical.trend
    :members: Slope

.. automodule:: pyalgotrade.technical.cross
    :members: cross_above, cross_below

.. automodule:: pyalgotrade.technical.linebreak
    :members: Line, LineBreak

.. automodule:: pyalgotrade.technical.stats
    :members: StdDev

.. automodule:: pyalgotrade.technical.bollinger
    :members: BollingerBands

