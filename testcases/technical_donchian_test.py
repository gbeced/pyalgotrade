from . import common
from pyalgotrade.technical import donchian
from pyalgotrade import dataseries

opens = [118.86, 118.27, 117.4 , 117.26, 116.3 , 116.15, 117.24, 116.38,
        115.47, 114.63, 115.5 , 116.05, 114.59, 115.22, 116.21, 116.,
        113.19, 115.98, 116.56, 115.61, 115.8 , 114.9 , 115.24, 115.6 ,
        116.83, 116.11, 115.75, 115.43, 115.5 , 115.85, 117.67, 118.47,
        119.5 , 117.21, 117.44, 117.46, 116.35, 114.7 , 112.56, 107.69]
closes = [118.94, 117.89, 117.65, 116.56, 116.16, 117.36, 116.38, 115.88,
        116.18, 115.28, 115.9 , 114.96, 115.59, 116.1 , 115.81, 114.37,
        115.86, 116.6 , 115.89, 116.58, 114.49, 114.27, 115.27, 116.81,
        116.31, 116.45, 115.25, 115.4 , 115.85, 117.44, 117.89, 119.63,
        117.68, 117.69, 118.58, 116.32, 114.39, 113.78, 110.4 , 107.68]
highs = [119.89, 118.7886, 118.09, 117.515 , 116.73, 117.37,
        117.34, 116.55, 116.2099, 115.87, 115.93, 116.3,
        115.69, 116.53, 116.31, 116.03, 116.23, 116.9,
        117.12, 116.72, 116.2599, 115.39, 116.24, 116.95,
        117.23, 116.76, 116.98, 115.5, 116.42, 117.535 ,
        118.57, 119.95, 119.94, 118.11, 118.75, 118.46,
        117.07, 115.17, 114.07, 108.52]
lows = [118.7016, 117.59, 116.77, 116.2, 115.68, 116.0806,
        115.98, 115.37, 115.13, 114.52, 115.28, 114.64,
        114.5151, 115.18, 115.04, 114.15, 112.68, 115.9496,
        115.89, 115.3314, 113.9, 114.1, 114.89, 114.85,
        116.06, 115.76, 115.045, 114.44, 115.41, 115.5809,
        117.155, 117.36, 117.68, 116.86, 117.31, 115.952 ,
        114.05, 113.65, 110.35, 104.37]

upperExpected = [None, None, None, None, None, None,
    None, None, None, None, None, None,
    None, None, None, None, None, None,
    None, None, 119.89, 118.7886, 118.09, 117.515 ,
    117.37, 117.37, 117.34, 117.23, 117.23, 117.23,
    117.535 , 118.57, 119.95, 119.95, 119.95, 119.95,
    119.95, 119.95, 119.95, 119.95]

lowerExpected = [None, None, None, None, None, None, None, None,
        None, None, None, None, None, None, None, None,
        None, None, None, None, 112.68, 112.68, 112.68, 112.68,
        112.68, 112.68, 112.68, 112.68, 112.68, 112.68, 112.68, 112.68,
        112.68, 112.68, 112.68, 112.68, 112.68, 113.9 , 113.65, 110.35]

midExpected = [  None, None, None, None, None, None,
        None, None, None, None, None, None,
        None, None, None, None, None, None,
        None, None, 116.285 , 115.7343, 115.385 , 115.0975,
        115.025 , 115.025 , 115.01, 114.955 , 114.955 , 114.955 ,
        115.1075, 115.625 , 116.315 , 116.315 , 116.315 , 116.315 ,
        116.315 , 116.925 , 116.8, 115.15]

class DonchianTest(common.TestCase):
    def test0(self):
        barDS = bards.BarDataSeries()
        donDS = donchian.DonchianChannel(barDS, period)
        now = datetime(2020, 1, 1)
        for i, (o, h, l, c) in enumerate(zip(opens, highs, lows, close)):
            b = bar.BasicBar(now + timedelta(days=i), o, h, l, c, 100, c, bar.Frequency.DAY)
            barDS.append(b)
            # print(i, donDS.getUpperChannel()[i], upperExpected[i])
            self.assertEqual(common.safe_round(donDS.getUpperChannel()[i], upperExpected))
            self.assertEqual(common.safe_round(donDS.getLowerChannel()[i], lowerExpected))
            self.assertEqual(common.safe_round(donDS.getMiddleChannel()[i], midExpected))
