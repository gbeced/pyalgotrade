"""
.. moduleauthor:: Massimo Fierro <massimo.fierro@gmail.com>
"""

from pyalgotrade.stratanalyzer import returns


class ExtendedPositionTracker(PositionTracker):
    """
    An extended PositionTracker that also tracks entry/exit dates and prices,
    highest and lowest prices during posession, number of contracts and whether
    the position is a long or not.
    """

    def __init__(self, instrumentTraits):
        super(ExtendedPositionTracker, self).__init__(instrumentTraits)
        self._update = super(ExtendedPositionTracker, self).update
        self._buy = super(ExtendedPositionTracker, self).buy
        self._sell = super(ExtendedPositionTracker, self).sell

        self._high = 0.0
        self._low = 0.0
        self.entryDate = None
        self.exitDate = None
        self.entryPrice = 0.0
        self.exitPrice = 0.0
        self.isLong = False
        self.contracts = 0

    def reset(self):
        self._PositionTracker__pnl = 0.0
        self._PositionTracker__avgPrice = 0.0
        self._PositionTracker__position = 0.0
        self._PositionTracker__commissions = 0.0
        self._PositionTracker__totalCommited = 0.0

        self._high = 0.0
        self._low = 0.0
        self.entryDate = None
        self.exitDate = None
        self.entryPrice = 0.0
        self.exitPrice = 0.0
        self.isLong = None
        self.contracts = 0

    def update(self, quantity, price, commission):
        prevPos = self._PositionTracker__position

        self._update(quantity, price, commission)

        # Register the entry price and isLong flag
        if prevPos == 0:
            self.entryPrice = price
            if self._PositionTracker__position > 0:
                self.isLong = True
            else:
                self.isLong = False

        # Register the exit price
        if self._PositionTracker__position == 0:
            self.exitPrice = price
            self.contracts = prevPos

    def buy(self, quantity, price, commission=0.0):
        self._buy(quantity, price, commission)

    def sell(self, quantity, price, commission=0.0):
        self._sell(quantity, price, commission)

    def setHigh(self, high):
        if high > self._high or self._high == 0:
            self._high = high

    def setLow(self, low):
        if low < self._low or self._low == 0:
            self._low = low
