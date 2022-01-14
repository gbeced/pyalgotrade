import numpy as np
from pyalgotrade import technical
from pyalgotrade.utils import collections

class PSAREventWindow(technical.EventWindow):
    def __init__(self, init_acceleration_factor, acceleration_factor_step, max_acceleration_factor, previous_day, period):
        assert(period > 0)
        super(PSAREventWindow, self).__init__(period=2) # Different 'period' param than above 
        self.__value = None 
        self.__numDays = 0 

        self.init_acceleration_factor = init_acceleration_factor 
        self.acceleration_factor = init_acceleration_factor
        self.acceleration_factor_step = acceleration_factor_step
        self.max_acceleration_factor = max_acceleration_factor
        self.previous_day = previous_day 

        self.init_high_price = None
        self.init_low_price = None

        self.high_prices_trend = []
        self.low_prices_trend = []

        self.high_prices_window = collections.NumPyDeque(period, float)
        self.low_prices_window = collections.NumPyDeque(period, float)

        self.extreme_point = None 

        self.trend_type = None 

    def _calculatePSAR(self, value):
        psar= None
        if self.__numDays < 2:
            psar= None
            self.init_high_price = value.getHigh()
            self.init_low_price = value.getLow()
            self.high_prices_window.append(self.init_high_price)
            self.low_prices_window.append(self.init_low_price)

        elif self.__numDays == 2: 
            if  value.getHigh() > self.init_high_price:
                psar = min(self.init_low_price, value.getLow())
                self.trend_type = 'upward'
                self.extreme_point = value.getLow()
            else: 
                psar = max(self.init_high_price, value.getHigh())
                self.trend_type = 'downward'
                self.extreme_point = value.getHigh()

            self.high_prices_trend.append(value.getHigh())
            self.low_prices_trend.append(value.getLow())
            self.high_prices_window.append(value.getHigh())
            self.low_prices_window.append(value.getLow())

        else:
            prior_psar = self.getValues()[-1]
            if self.trend_type == 'upward': 
                extreme_point = np.max(self.high_prices_trend)
                if self.extreme_point != extreme_point: 
                    self.extreme_point = extreme_point 
                    self.acceleration_factor = min(self.acceleration_factor + self.acceleration_factor_step, self.max_acceleration_factor)
                psar = prior_psar + self.acceleration_factor * (self.extreme_point - prior_psar)
                psar = min(psar, min(self.low_prices_window)) # ensure that psar is lower than previous 'periods' days worth of lows 
                if psar > value.getLow(): # If today's psar is greater than today's low, that indicates reversal 
                    self.trend_type = 'downward'
                    self.high_prices_trend = []
                    self.low_prices_trend = []
                    self.accelaration_factor = self.init_acceleration_factor 
                    self.extreme_point = value.getHigh()

            elif self.trend_type == 'downward': 
                extreme_point = np.min(self.low_prices_trend)
                if self.extreme_point != extreme_point: 
                    self.extreme_point = extreme_point 
                    self.acceleration_factor = min(self.acceleration_factor + self.acceleration_factor_step, self.max_acceleration_factor)
                psar = prior_psar - self.acceleration_factor * (self.extreme_point - prior_psar) 
                psar = max(psar, max(self.high_prices_window)) # ensure that psar is higher than previous 'periods' days worth of lows 
                if psar < value.getHigh(): # if today's psar is lower than today's high, that indicates reversal
                    self.trend_type = 'upward'
                    self.high_prices_trend = []
                    self.low_prices_trend = []
                    self.accelaration_factor = self.init_acceleration_factor 
                    self.extreme_point = value.getLow()
            else: 
                pass 

            self.high_prices_trend.append(value.getHigh()) # append today's prices to the price trend list and price deque 
            self.low_prices_trend.append(value.getLow())
            self.high_prices_window.append(value.getHigh())
            self.low_prices_window.append(value.getLow())

        return psar 

    def onNewValue(self, dateTime, value):
        if value is not None:
            self.__numDays += 1 
            psar = self._calculatePSAR(value)
            if psar != None: 
                super(PSAREventWindow, self).onNewValue(dateTime, psar)
        if value is not None and self.windowFull():
            if self.previous_day:
                self.__value = self.getValues()[0] 
            else: 
                self.__value = self.getValues()[1]

    def getValue(self):
        return self.__value 

class PSAR(technical.EventBasedFilter):
    """Parabolic SAR Filter.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param init_acceleration_factor: Initial acceleration factor
    :type init_acceleration_factor: float.
    :param acceleration_factor_step: Step size for acceleration factor 
    :type acceleration_factor_step: float.
    :param max_acceleration_factor: Maximum allowable acceleration factor 
    :type max_acceleration_factor: float.
    :param previous_day: Whether or not previous day PSAR should be returned (if True), else return current day PSAR
    :type previous_day: bool.
    :param period: Number of days to look back to ensure PSAR in right range 
    :type period: int 
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.


    Use this logic to calcualte initial SAR: https://quant.stackexchange.com/questions/35570/how-do-you-calculate-the-initial-prior-sar-value-in-a-parabolic-sar-over-fx-mark

    See this link for PSAR explanation: https://books.mec.biz/tmp/books/218XOTBWY3FEW2CT3EVR.PDF 
    """
    def __init__(self, barDataSeries, init_acceleration_factor=0.02, acceleration_factor_step=0.02, max_acceleration_factor=0.2, previous_day=False, period=2, maxLen=None):
        #Period parameter below is NOT the same period above, below is for storing actual PSAR values
        super(PSAR, self).__init__(barDataSeries, PSAREventWindow(init_acceleration_factor, acceleration_factor_step, max_acceleration_factor, previous_day, period=2), maxLen)