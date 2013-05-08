from pyalgotrade import dataseries

# Build a sequence based DataSeries and put in some values.
ds = dataseries.SequenceDataSeries()
for i in range(0, 50):
	ds.append(i)

# Get the last value.
print ds[49]
print ds[-1]

# Get the previous value.
print ds[48]
print ds[-2]

# Get the first value.
print ds[0]
print ds[-50]

# Get the last 3 values.
print ds[-3:]
