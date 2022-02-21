
import numpy as np
from pyalgotrade import technical
from pyalgotrade.dataseries import bards

class PRICEEventWindow(technical.EventWindow):
    def __init__(self, period=1, min_or_max="max"):
        assert(period > 0)
        super(PRICEEventWindow, self).__init__(period)
        self.__value = None
        self.min_or_max = min_or_max

    def onNewValue(self, dateTime, value):
        firstValue = None
        if len(self.getValues()) > 0:
            firstValue = self.getValues()[0]
            assert(firstValue is not None)

        super(PRICEEventWindow, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            if self.min_or_max == "max":
                self.__value = self.getValues().max()
            elif self.min_or_max == "min":
                self.__value = self.getValues().min()
            else:
                print("Please set 'min_or_max' to either 'min' or 'max'")

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

        super(PRICE, self).__init__(dataSeries, PRICEEventWindow(period=1), maxLen)
        
class PRICE_WINDOW(technical.EventBasedFilter):
    """PRICE_WINDOW filter.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param period: Number of periods to look back at prices
    :type period: int
    :param max_or_min: Whether to take max or minimum of price over window 
    :type max_or_min: str
    :param price_type: Type of price - "High", "Low", or "Close" (always Adj Close) to use for Price 
    :type price_type: str  
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, barDataSeries, period=30, max_or_min="max", price_type="High", maxLen=None):
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

        super(PRICE_WINDOW, self).__init__(dataSeries, PRICEEventWindow(period=period, max_or_min=max_or_min), maxLen)