TA-Lib integration
==================

The **pyalgotrade.talibext.indicator** module provides integration with Python wrapper for TA-Lib (http://mrjbq7.github.com/ta-lib/)
to enable calling TA-Lib functions directly with :class:`pyalgotrade.dataseries.DataSeries` or :class:`pyalgotrade.dataseries.bards.BarDataSeries`
instances instead of numpy arrays.

If you're familiar with the **talib** module, then using the **pyalgotrade.talibext.indicator** module should be straightforward.
When using **talib** standalone you do something like this: ::

    import numpy
    import talib

    data = numpy.random.random(100)
    upper, middle, lower = talib.BBANDS(data, matype=talib.MA_T3)

To use the **pyalgotrade.talibext.indicator** module in your strategies you should do something like this: ::

    def onBars(self, bars):
        closeDs = self.getFeed().getDataSeries("orcl").getCloseDataSeries()
        upper, middle, lower = pyalgotrade.talibext.indicator.BBANDS(closeDs, 100, matype=talib.MA_T3)
        if upper != None:
            print "%s" % upper[-1]

Every function in the **pyalgotrade.talibext.indicator** module receives one or more dataseries (most receive just one) and the
number of values to use from the dataseries. In the example above, we're calculating Bollinger Bands over the last 100 closing prices.

If the parameter name is **ds**, then you should pass a regular :class:`pyalgotrade.dataseries.DataSeries` instance, like the one
shown in the example above.

If the parameter name is **barDs**, then you should pass a :class:`pyalgotrade.dataseries.bards.BarDataSeries` instance, like in the next
example: ::

    def onBars(self, bars):
        barDs = self.getFeed().getDataSeries("orcl")
        sar = indicator.SAR(barDs, 100)
        if sar != None:
            print "%s" % sar[-1]

The following TA-Lib functions are available through the **pyalgotrade.talibext.indicator** module:

.. automodule:: pyalgotrade.talibext.indicator
    :members:
    :member-order: bysource
    :show-inheritance:

