from pyalgotrade import dataseries
from pyalgotrade import technical


# An EventWindow is responsible for making calculations using a window of values.
class Accumulator(technical.EventWindow):
    def getValue(self):
        ret = None
        if self.windowFull():
            ret = self.getValues().sum()
        return ret

# Build a sequence based DataSeries.
seqDS = dataseries.SequenceDataSeries()
# Wrap it with a filter that will get fed as new values get added to the underlying DataSeries.
accum = technical.EventBasedFilter(seqDS, Accumulator(3))

# Put in some values.
for i in range(0, 50):
    seqDS.append(i)

# Get some values.
print accum[0]  # Not enough values yet.
print accum[1]  # Not enough values yet.
print accum[2]  # Ok, now we should have at least 3 values.
print accum[3]

# Get the last value, which should be equal to 49 + 48 + 47.
print accum[-1]
