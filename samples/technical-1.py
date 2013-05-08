from pyalgotrade import dataseries
from pyalgotrade import technical

class Accumulator(technical.DataSeriesFilter):
    def __init__(self, dataSeries, windowSize):
        technical.DataSeriesFilter.__init__(self, dataSeries, windowSize)

    def calculateValue(self, firstPos, lastPos):
        accum = 0
        for value in self.getDataSeries()[firstPos:lastPos+1]:
            # If any value from the wrapped DataSeries is None then we abort calculation and return None.
            if value is None:
                return None
            accum += value
        return accum

# Build a sequence based DataSeries and wrap it with a 3 element Accumulator filter.
seqDS = dataseries.SequenceDataSeries()
ds = Accumulator(seqDS, 3)

# Put in some values.
for i in range(0, 50):
	seqDS.append(i)

# Get some values.
print ds[0] # Not enough values yet.
print ds[1] # Not enough values yet.
print ds[2] # Ok, now we should have at least 3 values.
print ds[3]

# Get the last value, which should equals 49 + 48 + 47.
print ds[-1]


