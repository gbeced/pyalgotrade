from pyalgotrade import technical
from pyalgotrade.dataseries import bards
import numpy as np 



class STOP_PRICEEventWindow_Frac(technical.EventWindow):
    def __init__(self, percent_change, period, entry_price):
        assert(period > 0)
        super(STOP_PRICEEventWindow_Frac, self).__init__(period)
        self.__value = None
        self.percent_change = percent_change
        self.__entry_price = entry_price

    def onNewValue(self, dateTime, value):
        firstValue = None
        if len(self.getValues()) > 0:
            firstValue = self.getValues()[0]
            assert(firstValue is not None)

        super(STOP_PRICEEventWindow_Frac, self).onNewValue(dateTime, value)

        if value is not None and not np.isnan(value) and self.windowFull():
            if self.__value is None or np.isnan(self.__value):
                self.__value = self.getValues().mean()
            else:
                self.__value = self.__value + value / float(self.getWindowSize()) - firstValue / float(self.getWindowSize())

    def getValue(self):
        if self.__entry_price is not None: 
            return self.__entry_price * (self.percent_change + 100) / 100
        else: 
            return np.Inf * self.percent_change


class STOP_PRICE(technical.EventBasedFilter):
    """STOP_Price Indicator using SMA Filter for PRice. 

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param percent_change: Percent Change in entry price used to calculate STOP_PRICE = (percent_change + 100 ) / 100 * Price.
    :type percent_change: float.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, dataSeries, percent_change, trailing=False, entry_price=None, maxLen=None):
        assert percent_change >= -100, "percent_change must be greater than -100"
        self.percent_change = percent_change
        self.stop_loss = percent_change < 0
        self.stop_profit = percent_change >= 0
        self.trailing = trailing
        super(STOP_PRICE, self).__init__(dataSeries, STOP_PRICEEventWindow_Frac(percent_change, period=1, entry_price=entry_price), maxLen)



class ATR_STOP_PRICEEventWindow_Frac(technical.EventWindow):
    def __init__(self, period, entry_price, stop_price_ATR_frac, useAdjustedValues):
        assert(period > 1)
        super(ATR_STOP_PRICEEventWindow_Frac, self).__init__(period)
        self.__useAdjustedValues = useAdjustedValues
        self.__entry_price = entry_price
        self.__stop_price_ATR_frac = stop_price_ATR_frac
        self.__prevClose = None
        self.__value = None


    def _calculateTrueRange(self, value):
        ret = None
        if self.__prevClose is None:
            ret = value.getHigh(self.__useAdjustedValues) - value.getLow(self.__useAdjustedValues)
        else:
            tr1 = value.getHigh(self.__useAdjustedValues) - value.getLow(self.__useAdjustedValues)
            tr2 = abs(value.getHigh(self.__useAdjustedValues) - self.__prevClose)
            tr3 = abs(value.getLow(self.__useAdjustedValues) - self.__prevClose)
            ret = max(max(tr1, tr2), tr3)
        return ret

    def onNewValue(self, dateTime, value):
        tr = self._calculateTrueRange(value)
        super(ATR_STOP_PRICEEventWindow_Frac, self).onNewValue(dateTime, tr)
        self.__prevClose = value.getClose(self.__useAdjustedValues)

        if value is not None and self.windowFull():
            if self.__value is None or np.isnan(self.__value):
                self.__value = self.getValues().mean() 
            else:
                self.__value = (self.__value * (self.getWindowSize() - 1) + tr) / float(self.getWindowSize())

    def getValue(self):
        if self.__value is not None: 
            if self.__entry_price is not None: 
                return self.__entry_price + self.__value * self.__stop_price_ATR_frac
            else: 
                return np.Inf * self.__stop_price_ATR_frac
        else: 
            return np.Inf * self.__stop_price_ATR_frac
        ## TODO, ensure that data feed goes back far enough in time to calculate ATR for stop price, for now just return inf

class ATR_STOP_PRICE(technical.EventBasedFilter): 
    '''ATR_STOP_PRICE Indicator using SMA Filter for Price. 

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param period: Number of days to look back to calculate ATR.
    :type period: int. 
    :param entry_price: The price at which a position was opened.
    :type entry_price: float. 
    :param stop_price_ATR_frac: The number of ATR multiples away from entry_price to use as ATR_STOP_PRICE. (positive if stop profit, else stop loss)
    :type stop_price_ATR_frac: float.     
    '''
    def __init__(self, barDataSeries, period=20, trailing=False, entry_price=None, stop_price_ATR_frac=-2, useAdjustedValues=True, maxLen=None): 
        self.stop_loss = stop_price_ATR_frac < 0
        self.stop_profit = stop_price_ATR_frac >= 0
        self.trailing = trailing 
        if not isinstance(barDataSeries, bards.BarDataSeries):
            raise Exception("barDataSeries must be a dataseries.bards.BarDataSeries instance")

        super(ATR_STOP_PRICE, self).__init__(barDataSeries, ATR_STOP_PRICEEventWindow_Frac(period, entry_price, stop_price_ATR_frac, useAdjustedValues), maxLen)
