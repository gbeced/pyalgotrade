technical -- Technical indicators
=================================

.. automodule:: pyalgotrade.technical
    :members: EventWindow, EventBasedFilter
    :show-inheritance:

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
    :show-inheritance:

.. automodule:: pyalgotrade.technical.vwap
    :members: VWAP
    :show-inheritance:

Momentum Indicators
-------------------

.. automodule:: pyalgotrade.technical.macd
    :members: MACD
    :show-inheritance:

.. automodule:: pyalgotrade.technical.rsi
    :members: RSI
    :show-inheritance:

.. automodule:: pyalgotrade.technical.stoch
    :members: StochasticOscillator
    :show-inheritance:

.. automodule:: pyalgotrade.technical.roc
    :members: RateOfChange
    :show-inheritance:

Other Indicators
----------------

.. automodule:: pyalgotrade.technical.atr
    :members: ATR
    :show-inheritance:

.. automodule:: pyalgotrade.technical.bollinger
    :members: BollingerBands
    :show-inheritance:

.. automodule:: pyalgotrade.technical.cross
    :members: cross_above, cross_below
    :show-inheritance:

.. automodule:: pyalgotrade.technical.cumret
    :members: CumulativeReturn
    :show-inheritance:

.. automodule:: pyalgotrade.technical.highlow
    :members: High, Low
    :show-inheritance:

.. automodule:: pyalgotrade.technical.hurst
    :members: HurstExponent
    :show-inheritance:

.. automodule:: pyalgotrade.technical.linebreak
    :members: Line, LineBreak
    :show-inheritance:

.. automodule:: pyalgotrade.technical.linreg
    :members: LeastSquaresRegression, Slope
    :show-inheritance:

.. automodule:: pyalgotrade.technical.stats
    :members: StdDev, ZScore
    :show-inheritance:

