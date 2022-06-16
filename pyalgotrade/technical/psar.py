import numpy as np
from pyalgotrade import technical
from pyalgotrade.utils import collections

class PSAREventWindow(technical.EventWindow):
    def __init__(self, type_indicator, init_acceleration_factor, acceleration_factor_step, max_acceleration_factor, 
                 period, useAdjustedValues):
        assert(period > 0)
        super(PSAREventWindow, self).__init__(windowSize=2) # Keeps track of current and pervious PSAR values
        self.__value = None 
        self.__numDays = 0 
        self.__useAdjustedValues = useAdjustedValues
        self.type_indicator = type_indicator

        self.init_acceleration_factor = init_acceleration_factor 
        self.acceleration_factor = init_acceleration_factor
        self.acceleration_factor_step = acceleration_factor_step
        self.max_acceleration_factor = max_acceleration_factor

        self.high_prices_trend = []
        self.low_prices_trend = []

        self.high_prices_window = collections.NumPyDeque(period, float)
        self.low_prices_window = collections.NumPyDeque(period, float)

        self.extreme_point = None 

        self.trend_type = None 
        
        self.reversal_toUptrend = False 
        self.reversal_toDowntrend = False 

    def _calculatePSAR(self, value):
        psar= None
        if self.__numDays < 3:
            psar = None
            self.high_prices_window.append(value.getHigh(self.__useAdjustedValues))
            self.low_prices_window.append(value.getLow(self.__useAdjustedValues))

        elif self.__numDays == 3: 
            if  self.high_prices_window[1] > self.high_prices_window[0]:
                psar = min(self.low_prices_window)
                self.trend_type = 'upward'
                self.extreme_point = max(self.high_prices_window)
            else: 
                psar = max(self.high_prices_window)
                self.trend_type = 'downward'
                self.extreme_point = min(self.low_prices_window)

            self.high_prices_trend.append(value.getHigh(self.__useAdjustedValues))
            self.low_prices_trend.append(value.getLow(self.__useAdjustedValues))
            self.high_prices_window.append(value.getHigh(self.__useAdjustedValues))
            self.low_prices_window.append(value.getLow(self.__useAdjustedValues))

        else:
            prior_psar = self.getValues()[-1]
            if self.trend_type == 'upward': 
                extreme_point = np.max(self.high_prices_trend)
                if self.extreme_point != extreme_point: 
                    self.extreme_point = extreme_point 
                    self.acceleration_factor = min(self.acceleration_factor + self.acceleration_factor_step, self.max_acceleration_factor)
                psar = prior_psar + self.acceleration_factor * (self.extreme_point - prior_psar)
                psar = min(psar, min(self.low_prices_window)) # ensure that psar is lower than previous 'periods' days worth of lows 
                if psar > value.getLow(self.__useAdjustedValues): # If today's psar is greater than today's low, that indicates reversal 
                    self.trend_type = 'downward'
                    psar = np.max(self.high_prices_trend) ##set current day's psar to high of previous trend
                    self.high_prices_trend = []
                    self.low_prices_trend = []
                    self.accelaration_factor = self.init_acceleration_factor 
                    self.extreme_point = value.getLow(self.__useAdjustedValues)
                    self.reversal_toDowntrend = True 
                    self.reversal_toUptrend = False 
                else: 
                    self.reversal_toDowntrend = False 
                    self.reversal_toUptrend = False 

            elif self.trend_type == 'downward': 
                extreme_point = np.min(self.low_prices_trend)
                if self.extreme_point != extreme_point: 
                    self.extreme_point = extreme_point 
                    self.acceleration_factor = min(self.acceleration_factor + self.acceleration_factor_step, self.max_acceleration_factor)
                psar = prior_psar - self.acceleration_factor * (prior_psar - self.extreme_point) 
                psar = max(psar, max(self.high_prices_window)) # ensure that psar is higher than previous 'periods' days worth of highs 
                if psar < value.getHigh(self.__useAdjustedValues): # if today's psar is lower than today's high, that indicates reversal
                    self.trend_type = 'upward'
                    psar = np.min(self.low_prices_trend)
                    self.high_prices_trend = []
                    self.low_prices_trend = []
                    self.accelaration_factor = self.init_acceleration_factor 
                    self.extreme_point = value.getHigh(self.__useAdjustedValues)
                    self.reversal_toUptrend = True 
                    self.reversal_toDowntrend = False
                else:
                    self.reversal_toUptrend = False 
                    self.reversal_toDowntrend = False
            else: 
                pass 

            self.high_prices_trend.append(value.getHigh(self.__useAdjustedValues)) # append today's prices to the price trend list and price deque 
            self.low_prices_trend.append(value.getLow(self.__useAdjustedValues))
            self.high_prices_window.append(value.getHigh(self.__useAdjustedValues))
            self.low_prices_window.append(value.getLow(self.__useAdjustedValues))

        return psar 

    def onNewValue(self, dateTime, value):
        if value is not None:
            self.__numDays += 1 
            psar = self._calculatePSAR(value)
            if psar != None: 
                super(PSAREventWindow, self).onNewValue(dateTime, psar)
        if value is not None and self.windowFull():
            self.__value = self.getValues()[1]

    def getValue(self):
        if self.type_indicator == 'value':
            return self.__value 
        elif self.type_indicator == 'reversal_toUptrend': 
            return self.reversal_toUptrend
        elif self.type_indicator == 'reversal_toDowntrend':
            return self.reversal_toDowntrend
        else: 
            print("PSAR indicator type {self.type_indicator} not yet implemented.")
            return None 

class PSAR(technical.EventBasedFilter):
    """Parabolic SAR Filter.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param type_indicator: Indicates whether reversal signal should be returned or value of PSAR 
    :type type_indicator: str. 'value', 'reversal_toUptrend', 'reversal_toDowntrend' 
    :param init_acceleration_factor: Initial acceleration factor
    :type init_acceleration_factor: float.
    :param acceleration_factor_step: Step size for acceleration factor 
    :type acceleration_factor_step: float.
    :param max_acceleration_factor: Maximum allowable acceleration factor 
    :type max_acceleration_factor: float.
    :param period: Number of days to look back to ensure PSAR in right range 
    :type period: int 
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.


    Use this logic to calcualte initial SAR: https://quant.stackexchange.com/questions/35570/how-do-you-calculate-the-initial-prior-sar-value-in-a-parabolic-sar-over-fx-mark

    See this link for PSAR explanation: https://books.mec.biz/tmp/books/218XOTBWY3FEW2CT3EVR.PDF 
    """
    def __init__(self, barDataSeries, type_indicator='value', init_acceleration_factor=0.02, acceleration_factor_step=0.02, 
                 max_acceleration_factor=0.2, period=2, maxLen=None, useAdjustedValues=True):
        #Period parameter below is NOT the same period above, below is for storing actual PSAR values
        super(PSAR, self).__init__(barDataSeries, PSAREventWindow(type_indicator, init_acceleration_factor, acceleration_factor_step, max_acceleration_factor, period=2, useAdjustedValues=useAdjustedValues), maxLen)