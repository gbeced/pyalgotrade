
import numpy as np
from pyalgotrade import technical

class PRICEEventWindow(technical.EventWindow):
    def __init__(self, period=1):
        assert(period > 0)
        super(PRICEEventWindow, self).__init__(period=1)
        self.__value = None

    def onNewValue(self, dateTime, value):
        firstValue = None
        if len(self.getValues()) > 0:
            firstValue = self.getValues()[0]
            assert(firstValue is not None)

        super(PRICEEventWindow, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            if self.__value is None:
                self.__value = self.getValues().mean()
            else:
                self.__value = self.__value + value / float(self.getWindowSize()) - firstValue / float(self.getWindowSize())

    def getValue(self):
        return self.__value


class PRICE(technical.EventBasedFilter):
    """PRICE filter.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param price_type: Type of price - "High", "Low", or "Close" (always Adj Close) to use for Price 
    :type price_type: str 
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, barDataSeries, price_type="Close", maxLen=None):
        if not isinstance(barDataSeries, bards.BarDataSeries):
            raise Exception("barDataSeries must be a dataseries.bards.BarDataSeries instance")
        if price_type == "High":
            dataSeries = barDataSeries.getHighDataSeries()
        elif price_type == "Low": 
            dataSeries = barDataSeries.getLowDataSeries()
        elif price_type == "Close": 
            dataSeries = barDataSeries.getAdjCloseDataSeries()
        else: 
            pass 

        super(PRICE, self).__init__(dataSeries, PRICEventWindow(period=1), maxLen)