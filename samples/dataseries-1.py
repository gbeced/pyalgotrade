from pyalgotrade import dataseries

# Build a sequence based DataSeries.
ds = dataseries.SequenceDataSeries(range(0, 50))

# Get the last value.
print ds.getValue()
print ds.getValueAbsolute(49)
print ds[-1]
print ds[49]

# Get the previous value.
print ds.getValue(1)
print ds.getValueAbsolute(48)
print ds[-2]
print ds[48]

# Get the first value.
print ds.getValue(49)
print ds.getValueAbsolute(0)
print ds[-50]
print ds[0]


