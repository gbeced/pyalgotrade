# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import datetime
import talib

import common

from pyalgotrade.talibext import indicator
from pyalgotrade import bar
from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards


# Market data used for regression tests (252 price bars) extracted from ta-lib/src/tools/ta_regtest/test_data.c
OPEN_VALUES = [
    92.500000, 91.500000, 95.155000, 93.970000, 95.500000, 94.500000, 95.000000, 91.500000, 91.815000, 91.125000, 93.875000,
    97.500000, 98.815000, 92.000000, 91.125000, 91.875000, 93.405000, 89.750000, 89.345000, 92.250000, 89.780000,
    87.940000, 87.595000, 85.220000, 83.500000, 83.500000, 81.250000, 85.125000, 88.125000, 87.500000, 85.250000,
    86.000000, 87.190000, 86.125000, 89.000000, 88.625000, 86.000000, 85.500000, 84.750000, 85.250000, 84.250000,
    86.750000, 86.940000, 89.315000, 89.940000, 90.815000, 91.190000, 91.345000, 89.595000, 91.000000, 89.750000,
    88.750000, 88.315000, 84.345000, 83.500000, 84.000000, 86.000000, 85.530000, 87.500000, 88.500000, 90.000000,
    88.655000, 89.500000, 91.565000, 92.000000, 93.000000, 92.815000, 91.750000, 92.000000, 91.375000, 89.750000,
    88.750000, 85.440000, 83.500000, 84.875000, 98.625000, 96.690000, 102.375000, 106.000000, 104.625000, 102.500000,
    104.250000, 104.000000, 106.125000, 106.065000, 105.940000, 105.625000, 108.625000, 110.250000, 110.565000, 117.000000,
    120.750000, 118.000000, 119.125000, 119.125000, 117.815000, 116.375000, 115.155000, 111.250000, 111.500000, 116.690000,
    116.000000, 113.620000, 111.750000, 114.560000, 113.620000, 118.120000, 119.870000, 116.620000, 115.870000, 115.060000,
    115.870000, 117.500000, 119.870000, 119.250000, 120.190000, 122.870000, 123.870000, 122.250000, 123.120000, 123.310000,
    124.000000, 123.000000, 124.810000, 130.000000, 130.880000, 132.500000, 131.000000, 132.500000, 134.000000, 137.440000,
    135.750000, 138.310000, 138.000000, 136.380000, 136.500000, 132.000000, 127.500000, 127.620000, 124.000000, 123.620000,
    125.000000, 126.370000, 126.250000, 125.940000, 124.000000, 122.750000, 120.000000, 120.000000, 122.000000, 123.620000,
    121.500000, 120.120000, 123.750000, 122.750000, 125.000000, 128.500000, 128.380000, 123.870000, 124.370000, 122.750000,
    123.370000, 122.000000, 122.620000, 125.000000, 124.250000, 124.370000, 125.620000, 126.500000, 128.380000, 128.880000,
    131.500000, 132.500000, 137.500000, 134.630000, 132.000000, 134.000000, 132.000000, 131.380000, 126.500000, 128.750000,
    127.190000, 127.500000, 120.500000, 126.620000, 123.000000, 122.060000, 121.000000, 121.000000, 118.000000, 122.000000,
    122.250000, 119.120000, 115.000000, 113.500000, 114.000000, 110.810000, 106.500000, 106.440000, 108.000000, 107.000000,
    108.620000, 93.000000, 93.750000, 94.250000, 94.870000, 95.500000, 94.500000, 97.000000, 98.500000, 96.750000,
    95.870000, 94.440000, 92.750000, 90.500000, 95.060000, 94.620000, 97.500000, 96.000000, 96.000000, 94.620000,
    94.870000, 94.000000, 99.000000, 105.500000, 108.810000, 105.000000, 105.940000, 104.940000, 103.690000, 102.560000,
    103.440000, 109.810000, 113.000000, 117.000000, 116.250000, 120.500000, 111.620000, 108.120000, 110.190000, 107.750000,
    108.000000, 110.690000, 109.060000, 108.500000, 109.870000, 109.120000, 109.690000, 109.560000, 110.440000, 109.690000,
    109.190000]

HIGH_VALUES = [
    93.250000, 94.940000, 96.375000, 96.190000, 96.000000, 94.720000, 95.000000, 93.720000, 92.470000, 92.750000, 96.250000,
    99.625000, 99.125000, 92.750000, 91.315000, 93.250000, 93.405000, 90.655000, 91.970000, 92.250000, 90.345000,
    88.500000, 88.250000, 85.500000, 84.440000, 84.750000, 84.440000, 89.405000, 88.125000, 89.125000, 87.155000,
    87.250000, 87.375000, 88.970000, 90.000000, 89.845000, 86.970000, 85.940000, 84.750000, 85.470000, 84.470000,
    88.500000, 89.470000, 90.000000, 92.440000, 91.440000, 92.970000, 91.720000, 91.155000, 91.750000, 90.000000,
    88.875000, 89.000000, 85.250000, 83.815000, 85.250000, 86.625000, 87.940000, 89.375000, 90.625000, 90.750000,
    88.845000, 91.970000, 93.375000, 93.815000, 94.030000, 94.030000, 91.815000, 92.000000, 91.940000, 89.750000,
    88.750000, 86.155000, 84.875000, 85.940000, 99.375000, 103.280000, 105.375000, 107.625000, 105.250000, 104.500000,
    105.500000, 106.125000, 107.940000, 106.250000, 107.000000, 108.750000, 110.940000, 110.940000, 114.220000, 123.000000,
    121.750000, 119.815000, 120.315000, 119.375000, 118.190000, 116.690000, 115.345000, 113.000000, 118.315000, 116.870000,
    116.750000, 113.870000, 114.620000, 115.310000, 116.000000, 121.690000, 119.870000, 120.870000, 116.750000, 116.500000,
    116.000000, 118.310000, 121.500000, 122.000000, 121.440000, 125.750000, 127.750000, 124.190000, 124.440000, 125.750000,
    124.690000, 125.310000, 132.000000, 131.310000, 132.250000, 133.880000, 133.500000, 135.500000, 137.440000, 138.690000,
    139.190000, 138.500000, 138.130000, 137.500000, 138.880000, 132.130000, 129.750000, 128.500000, 125.440000, 125.120000,
    126.500000, 128.690000, 126.620000, 126.690000, 126.000000, 123.120000, 121.870000, 124.000000, 127.000000, 124.440000,
    122.500000, 123.750000, 123.810000, 124.500000, 127.870000, 128.560000, 129.630000, 124.870000, 124.370000, 124.870000,
    123.620000, 124.060000, 125.870000, 125.190000, 125.620000, 126.000000, 128.500000, 126.750000, 129.750000, 132.690000,
    133.940000, 136.500000, 137.690000, 135.560000, 133.560000, 135.000000, 132.380000, 131.440000, 130.880000, 129.630000,
    127.250000, 127.810000, 125.000000, 126.810000, 124.750000, 122.810000, 122.250000, 121.060000, 120.000000, 123.250000,
    122.750000, 119.190000, 115.060000, 116.690000, 114.870000, 110.870000, 107.250000, 108.870000, 109.000000, 108.500000,
    113.060000, 93.000000, 94.620000, 95.120000, 96.000000, 95.560000, 95.310000, 99.000000, 98.810000, 96.810000,
    95.940000, 94.440000, 92.940000, 93.940000, 95.500000, 97.060000, 97.500000, 96.250000, 96.370000, 95.000000,
    94.870000, 98.250000, 105.120000, 108.440000, 109.870000, 105.000000, 106.000000, 104.940000, 104.500000, 104.440000,
    106.310000, 112.870000, 116.500000, 119.190000, 121.000000, 122.120000, 111.940000, 112.750000, 110.190000, 107.940000,
    109.690000, 111.060000, 110.440000, 110.120000, 110.310000, 110.440000, 110.000000, 110.750000, 110.500000, 110.500000,
    109.500000]

LOW_VALUES = [
    90.750000, 91.405000, 94.250000, 93.500000, 92.815000, 93.500000, 92.000000, 89.750000, 89.440000, 90.625000, 92.750000,
    96.315000, 96.030000, 88.815000, 86.750000, 90.940000, 88.905000, 88.780000, 89.250000, 89.750000, 87.500000,
    86.530000, 84.625000, 82.280000, 81.565000, 80.875000, 81.250000, 84.065000, 85.595000, 85.970000, 84.405000,
    85.095000, 85.500000, 85.530000, 87.875000, 86.565000, 84.655000, 83.250000, 82.565000, 83.440000, 82.530000,
    85.065000, 86.875000, 88.530000, 89.280000, 90.125000, 90.750000, 89.000000, 88.565000, 90.095000, 89.000000,
    86.470000, 84.000000, 83.315000, 82.000000, 83.250000, 84.750000, 85.280000, 87.190000, 88.440000, 88.250000,
    87.345000, 89.280000, 91.095000, 89.530000, 91.155000, 92.000000, 90.530000, 89.970000, 88.815000, 86.750000,
    85.065000, 82.030000, 81.500000, 82.565000, 96.345000, 96.470000, 101.155000, 104.250000, 101.750000, 101.720000,
    101.720000, 103.155000, 105.690000, 103.655000, 104.000000, 105.530000, 108.530000, 108.750000, 107.750000, 117.000000,
    118.000000, 116.000000, 118.500000, 116.530000, 116.250000, 114.595000, 110.875000, 110.500000, 110.720000, 112.620000,
    114.190000, 111.190000, 109.440000, 111.560000, 112.440000, 117.500000, 116.060000, 116.560000, 113.310000, 112.560000,
    114.000000, 114.750000, 118.870000, 119.000000, 119.750000, 122.620000, 123.000000, 121.750000, 121.560000, 123.120000,
    122.190000, 122.750000, 124.370000, 128.000000, 129.500000, 130.810000, 130.630000, 132.130000, 133.880000, 135.380000,
    135.750000, 136.190000, 134.500000, 135.380000, 133.690000, 126.060000, 126.870000, 123.500000, 122.620000, 122.750000,
    123.560000, 125.810000, 124.620000, 124.370000, 121.810000, 118.190000, 118.060000, 117.560000, 121.000000, 121.120000,
    118.940000, 119.810000, 121.000000, 122.000000, 124.500000, 126.560000, 123.500000, 121.250000, 121.060000, 122.310000,
    121.000000, 120.870000, 122.060000, 122.750000, 122.690000, 122.870000, 125.500000, 124.250000, 128.000000, 128.380000,
    130.690000, 131.630000, 134.380000, 132.000000, 131.940000, 131.940000, 129.560000, 123.750000, 126.000000, 126.250000,
    124.370000, 121.440000, 120.440000, 121.370000, 121.690000, 120.000000, 119.620000, 115.500000, 116.750000, 119.060000,
    119.060000, 115.060000, 111.060000, 113.120000, 110.000000, 105.000000, 104.690000, 103.870000, 104.690000, 105.440000,
    107.000000, 89.000000, 92.500000, 92.120000, 94.620000, 92.810000, 94.250000, 96.250000, 96.370000, 93.690000,
    93.500000, 90.000000, 90.190000, 90.500000, 92.120000, 94.120000, 94.870000, 93.000000, 93.870000, 93.000000,
    92.620000, 93.560000, 98.370000, 104.440000, 106.000000, 101.810000, 104.120000, 103.370000, 102.120000, 102.250000,
    103.370000, 107.940000, 112.500000, 115.440000, 115.500000, 112.250000, 107.560000, 106.560000, 106.870000, 104.500000,
    105.750000, 108.620000, 107.750000, 108.060000, 108.000000, 108.190000, 108.120000, 109.060000, 108.750000, 108.560000,
    106.620000]

CLOSE_VALUES = [
    91.500000, 94.815000, 94.375000, 95.095000, 93.780000, 94.625000, 92.530000, 92.750000, 90.315000, 92.470000, 96.125000,
    97.250000, 98.500000, 89.875000, 91.000000, 92.815000, 89.155000, 89.345000, 91.625000, 89.875000, 88.375000,
    87.625000, 84.780000, 83.000000, 83.500000, 81.375000, 84.440000, 89.250000, 86.375000, 86.250000, 85.250000,
    87.125000, 85.815000, 88.970000, 88.470000, 86.875000, 86.815000, 84.875000, 84.190000, 83.875000, 83.375000,
    85.500000, 89.190000, 89.440000, 91.095000, 90.750000, 91.440000, 89.000000, 91.000000, 90.500000, 89.030000,
    88.815000, 84.280000, 83.500000, 82.690000, 84.750000, 85.655000, 86.190000, 88.940000, 89.280000, 88.625000,
    88.500000, 91.970000, 91.500000, 93.250000, 93.500000, 93.155000, 91.720000, 90.000000, 89.690000, 88.875000,
    85.190000, 83.375000, 84.875000, 85.940000, 97.250000, 99.875000, 104.940000, 106.000000, 102.500000, 102.405000,
    104.595000, 106.125000, 106.000000, 106.065000, 104.625000, 108.625000, 109.315000, 110.500000, 112.750000, 123.000000,
    119.625000, 118.750000, 119.250000, 117.940000, 116.440000, 115.190000, 111.875000, 110.595000, 118.125000, 116.000000,
    116.000000, 112.000000, 113.750000, 112.940000, 116.000000, 120.500000, 116.620000, 117.000000, 115.250000, 114.310000,
    115.500000, 115.870000, 120.690000, 120.190000, 120.750000, 124.750000, 123.370000, 122.940000, 122.560000, 123.120000,
    122.560000, 124.620000, 129.250000, 131.000000, 132.250000, 131.000000, 132.810000, 134.000000, 137.380000, 137.810000,
    137.880000, 137.250000, 136.310000, 136.250000, 134.630000, 128.250000, 129.000000, 123.870000, 124.810000, 123.000000,
    126.250000, 128.380000, 125.370000, 125.690000, 122.250000, 119.370000, 118.500000, 123.190000, 123.500000, 122.190000,
    119.310000, 123.310000, 121.120000, 123.370000, 127.370000, 128.500000, 123.870000, 122.940000, 121.750000, 124.440000,
    122.000000, 122.370000, 122.940000, 124.000000, 123.190000, 124.560000, 127.250000, 125.870000, 128.860000, 132.000000,
    130.750000, 134.750000, 135.000000, 132.380000, 133.310000, 131.940000, 130.000000, 125.370000, 130.130000, 127.120000,
    125.190000, 122.000000, 125.000000, 123.000000, 123.500000, 120.060000, 121.000000, 117.750000, 119.870000, 122.000000,
    119.190000, 116.370000, 113.500000, 114.250000, 110.000000, 105.060000, 107.000000, 107.870000, 107.000000, 107.120000,
    107.000000, 91.000000, 93.940000, 93.870000, 95.500000, 93.000000, 94.940000, 98.250000, 96.750000, 94.810000,
    94.370000, 91.560000, 90.250000, 93.940000, 93.620000, 97.000000, 95.000000, 95.870000, 94.060000, 94.620000,
    93.750000, 98.000000, 103.940000, 107.870000, 106.060000, 104.500000, 105.000000, 104.190000, 103.060000, 103.420000,
    105.270000, 111.870000, 116.000000, 116.620000, 118.280000, 113.370000, 109.000000, 109.700000, 109.250000, 107.000000,
    109.190000, 110.000000, 109.200000, 110.120000, 108.000000, 108.620000, 109.750000, 109.810000, 109.000000, 108.750000,
    107.870000]

VOLUME_VALUES = [
    4077500, 4955900, 4775300, 4155300, 4593100, 3631300, 3382800, 4954200, 4500000, 3397500, 4204500,
    6321400, 10203600, 19043900, 11692000, 9553300, 8920300, 5970900, 5062300, 3705600, 5865600,
    5603000, 5811900, 8483800, 5995200, 5408800, 5430500, 6283800, 5834800, 4515500, 4493300,
    4346100, 3700300, 4600200, 4557200, 4323600, 5237500, 7404100, 4798400, 4372800, 3872300,
    10750800, 5804800, 3785500, 5014800, 3507700, 4298800, 4842500, 3952200, 3304700, 3462000,
    7253900, 9753100, 5953000, 5011700, 5910800, 4916900, 4135000, 4054200, 3735300, 2921900,
    2658400, 4624400, 4372200, 5831600, 4268600, 3059200, 4495500, 3425000, 3630800, 4168100,
    5966900, 7692800, 7362500, 6581300, 19587700, 10378600, 9334700, 10467200, 5671400, 5645000,
    4518600, 4519500, 5569700, 4239700, 4175300, 4995300, 4776600, 4190000, 6035300, 12168900,
    9040800, 5780300, 4320800, 3899100, 3221400, 3455500, 4304200, 4703900, 8316300, 10553900,
    6384800, 7163300, 7007800, 5114100, 5263800, 6666100, 7398400, 5575000, 4852300, 4298100,
    4900500, 4887700, 6964800, 4679200, 9165000, 6469800, 6792000, 4423800, 5231900, 4565600,
    6235200, 5225900, 8261400, 5912500, 3545600, 5714500, 6653900, 6094500, 4799200, 5050800,
    5648900, 4726300, 5585600, 5124800, 7630200, 14311600, 8793600, 8874200, 6966600, 5525500,
    6515500, 5291900, 5711700, 4327700, 4568000, 6859200, 5757500, 7367000, 6144100, 4052700,
    5849700, 5544700, 5032200, 4400600, 4894100, 5140000, 6610900, 7585200, 5963100, 6045500,
    8443300, 6464700, 6248300, 4357200, 4774700, 6216900, 6266900, 5584800, 5284500, 7554500,
    7209500, 8424800, 5094500, 4443600, 4591100, 5658400, 6094100, 14862200, 7544700, 6985600,
    8093000, 7590000, 7451300, 7078000, 7105300, 8778800, 6643900, 10563900, 7043100, 6438900,
    8057700, 14240000, 17872300, 7831100, 8277700, 15017800, 14183300, 13921100, 9683000, 9187300,
    11380500, 69447300, 26673600, 13768400, 11371600, 9872200, 9450500, 11083300, 9552800, 11108400,
    10374200, 16701900, 13741900, 8523600, 9551900, 8680500, 7151700, 9673100, 6264700, 8541600,
    8358000, 18720800, 19683100, 13682500, 10668100, 9710600, 3113100, 5682000, 5763600, 5340000,
    6220800, 14680500, 9933000, 11329500, 8145300, 16644700, 12593800, 7138100, 7442300, 9442300,
    7123600, 7680600, 4839800, 4775500, 4008800, 4533600, 3741100, 4084800, 2685200, 3438000,
    2870500]

SAR_HIGH = [51.12, 52.35, 52.1, 51.8, 52.1, 52.5, 52.8, 52.5, 53.5, 53.5, 53.8, 54.2, 53.4, 53.5, 54.4, 55.2, 55.7, 57, 57.5, 58, 57.7, 58, 57.5, 57, 56.7, 57.5, 56.70, 56.00, 56.20, 54.80, 55.50, 54.70, 54.00, 52.50, 51.00, 51.50, 51.70, 53.00]
SAR_LOW = [50.0, 51.5, 51, 50.5, 51.25, 51.7, 51.85, 51.5, 52.3, 52.5, 53, 53.5, 52.5, 52.1, 53, 54, 55, 56, 56.5, 57, 56.5, 57.3, 56.7, 56.3, 56.2, 56, 55.50, 55.00, 54.90, 54.00, 54.50, 53.80, 53.00, 51.50, 50.00, 50.50, 50.20, 51.50]


def compare(obtained, expected, decimals=2):
    obtained = round(obtained, decimals)
    expected = round(expected, decimals)
    return obtained == expected


class TestCase(common.TestCase):
    TestInstrument = "orcl"

    def __loadMedPriceDS(self):
        ret = dataseries.SequenceDataSeries()
        for i in xrange(len(OPEN_VALUES)):
            ret.append(LOW_VALUES[i] + (HIGH_VALUES[i] - LOW_VALUES[i]) / 2.0)
        return ret

    def __loadBarDS(self):
        seconds = 0

        ret = bards.BarDataSeries()
        for i in xrange(len(OPEN_VALUES)):
            dateTime = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            ret.append(bar.BasicBar(dateTime, OPEN_VALUES[i], HIGH_VALUES[i], LOW_VALUES[i], CLOSE_VALUES[i], VOLUME_VALUES[i], CLOSE_VALUES[i], bar.Frequency.DAY))
            seconds += 1
        return ret

    def __loadSarTestBarDs(self):
        seconds = 0

        ret = bards.BarDataSeries()
        for i in xrange(len(SAR_HIGH)):
            dateTime = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            ret.append(bar.BasicBar(dateTime, SAR_LOW[i], SAR_HIGH[i], SAR_LOW[i], SAR_HIGH[i], 0, SAR_LOW[i], bar.Frequency.DAY))
            seconds += 1
        return ret

    def testAD(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.AD(barDs, 252)[0], -1631000.00))
        self.assertTrue(compare(indicator.AD(barDs, 252)[1], 2974412.02))
        self.assertTrue(compare(indicator.AD(barDs, 252)[-2], 8707691.07))
        self.assertTrue(compare(indicator.AD(barDs, 252)[-1], 8328944.54))

    def testADOSC(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ADOSC(barDs, 252, 3, 10)[9], 841238.33))  # Original value was 841238.32
        self.assertTrue(compare(indicator.ADOSC(barDs, 252, 3, 10)[9+1], 2255663.07))
        self.assertTrue(compare(indicator.ADOSC(barDs, 252, 3, 10)[-2], -526700.32))
        self.assertTrue(compare(indicator.ADOSC(barDs, 252, 3, 10)[-1], -1139932.729))

    def testADX(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ADX(barDs, 252, 14)[27], 23.0000))
        self.assertTrue(compare(indicator.ADX(barDs, 252, 14)[28], 22.0802))
        self.assertTrue(compare(indicator.ADX(barDs, 252, 14)[-2], 16.6840))
        self.assertTrue(compare(indicator.ADX(barDs, 252, 14)[-1], 15.5260))

    def testADXR(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ADXR(barDs, 252, 14)[40], 19.8666))
        self.assertTrue(compare(indicator.ADXR(barDs, 252, 14)[41], 18.9092))
        self.assertTrue(compare(indicator.ADXR(barDs, 252, 14)[-2], 21.5972))
        self.assertTrue(compare(indicator.ADXR(barDs, 252, 14)[-1], 20.4920))

    def testAPO(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.APO(barDs.getCloseDataSeries(), 252, 26, 12, talib.MA_Type.SMA)[25], -3.3124))
        self.assertTrue(compare(indicator.APO(barDs.getCloseDataSeries(), 252, 12, 26, talib.MA_Type.SMA)[25], -3.3124))
        self.assertTrue(compare(indicator.APO(barDs.getCloseDataSeries(), 252, 12, 26, talib.MA_Type.SMA)[26], -3.5876))
        self.assertTrue(compare(indicator.APO(barDs.getCloseDataSeries(), 252, 12, 26, talib.MA_Type.SMA)[-1], -0.1667))

    def testAROON(self):
        barDs = self.__loadBarDS()
        # AROON DOWN TEST
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[0][14], 100))
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[0][14+1], 92.857))
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[0][-2], 28.571))
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[0][-1], 21.429))
        # AROON UP TEST
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[1][14], 78.571))
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[1][14+1], 71.429))
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[1][-2], 0))
        self.assertTrue(compare(indicator.AROON(barDs, 252, 14)[1][-1], 7.1429))

    def testAROONOSC(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.AROONOSC(barDs, 252, 14)[14], -21.4285))
        self.assertTrue(compare(indicator.AROONOSC(barDs, 252, 14)[14+6], -21.4285))
        self.assertTrue(compare(indicator.AROONOSC(barDs, 252, 14)[14+7], -71.4285))
        self.assertTrue(compare(indicator.AROONOSC(barDs, 252, 14)[-2], -28.5714))
        self.assertTrue(compare(indicator.AROONOSC(barDs, 252, 14)[-1], -14.28571))

    def testATR(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ATR(barDs, 252, 1)[1], 3.535, 3))
        self.assertTrue(compare(indicator.ATR(barDs, 252, 1)[13], 9.685, 3))
        self.assertTrue(compare(indicator.ATR(barDs, 252, 1)[41], 5.125, 3))
        self.assertTrue(compare(indicator.ATR(barDs, 252, 1)[-1], 2.88, 3))

    def testAVGPRICE(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.AVGPRICE(barDs, 252)[0], 92.0))
        self.assertTrue(compare(indicator.AVGPRICE(barDs, 252)[1], 93.16))  # Original value was 93.17

    def testBBANDS(self):
        barDs = self.__loadBarDS()
        # EMA
        self.assertTrue(compare(indicator.BBANDS(barDs.getCloseDataSeries(), 252, 20, 2.0, 2.0, talib.MA_Type.EMA)[0][19+13], 93.674))
        self.assertTrue(compare(indicator.BBANDS(barDs.getCloseDataSeries(), 252, 20, 2.0, 2.0, talib.MA_Type.EMA)[1][19+13], 87.679))
        self.assertTrue(compare(indicator.BBANDS(barDs.getCloseDataSeries(), 252, 20, 2.0, 2.0, talib.MA_Type.EMA)[2][19+13], 81.685))
        # SMA
        self.assertTrue(compare(indicator.BBANDS(barDs.getCloseDataSeries(), 252, 20, 2.0, 2.0, talib.MA_Type.SMA)[0][19], 98.0734))
        self.assertTrue(compare(indicator.BBANDS(barDs.getCloseDataSeries(), 252, 20, 2.0, 2.0, talib.MA_Type.SMA)[1][19], 92.8910))
        self.assertTrue(compare(indicator.BBANDS(barDs.getCloseDataSeries(), 252, 20, 2.0, 2.0, talib.MA_Type.SMA)[2][19], 87.7086))

    def testBETA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.BETA(barDs.getHighDataSeries(), barDs.getLowDataSeries(), 252, 5)[5], 0.62907))
        self.assertTrue(compare(indicator.BETA(barDs.getHighDataSeries(), barDs.getLowDataSeries(), 252, 5)[6], 0.83604))

    def testBOP(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.BOP(barDs, 252)[0], -0.40))
        self.assertTrue(compare(indicator.BOP(barDs, 252)[1], 0.94))

    def testCCI(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.CCI(barDs, 252, 2)[1], 66.666))
        self.assertTrue(compare(indicator.CCI(barDs, 252, 5)[4], 18.857))
        self.assertTrue(compare(indicator.CCI(barDs, 252, 11)[10], 87.927))
        self.assertTrue(compare(indicator.CCI(barDs, 252, 11)[11], 180.005, 3))

    def testCMO(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.CMO(barDs.getCloseDataSeries(), 252, 14)[14], -1.70, 1))

    def testCORREL(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.CORREL(barDs.getHighDataSeries(), barDs.getLowDataSeries(), 252, 20)[19], 0.9401569))
        self.assertTrue(compare(indicator.CORREL(barDs.getHighDataSeries(), barDs.getLowDataSeries(), 252, 20)[20], 0.9471812))
        self.assertTrue(compare(indicator.CORREL(barDs.getHighDataSeries(), barDs.getLowDataSeries(), 252, 20)[-1], 0.8866901))

    def testDX(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.DX(barDs, 252, 14)[14], 19.3689))
        self.assertTrue(compare(indicator.DX(barDs, 252, 14)[15], 9.7131))
        self.assertTrue(compare(indicator.DX(barDs, 252, 14)[16], 17.2905))
        self.assertTrue(compare(indicator.DX(barDs, 252, 14)[-2], 10.6731))
        self.assertTrue(compare(indicator.DX(barDs, 252, 14)[-1], 0.4722))

    def testEMA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.EMA(barDs.getCloseDataSeries(), 252, 2)[1], 93.16))  # Original value 93.15
        self.assertTrue(compare(indicator.EMA(barDs.getCloseDataSeries(), 252, 2)[2], 93.97))  # Original value 93.96
        self.assertTrue(compare(indicator.EMA(barDs.getCloseDataSeries(), 252, 2)[-1], 108.22))  # Original value 108.21
        self.assertTrue(compare(indicator.EMA(barDs.getCloseDataSeries(), 252, 10)[9], 93.23))  # Original value 93.22

    def testHT_DCPERIOD(self):
        ds = self.__loadMedPriceDS()
        self.assertTrue(compare(indicator.HT_DCPERIOD(ds, 252)[32], 15.5527, 4))
        self.assertTrue(compare(indicator.HT_DCPERIOD(ds, 252)[-1], 18.6140, 4))

    def testHT_DCPHASE(self):
        ds = self.__loadMedPriceDS()
        self.assertTrue(compare(indicator.HT_DCPHASE(ds, 252)[63], 22.1496, 4))  # Original value 22.1495
        self.assertTrue(compare(indicator.HT_DCPHASE(ds, 252)[-3], -31.182, 3))
        self.assertTrue(compare(indicator.HT_DCPHASE(ds, 252)[-2], 23.2691, 4))
        self.assertTrue(compare(indicator.HT_DCPHASE(ds, 252)[-1], 47.2765, 4))

    def testHT_TRENDLINE(self):
        ds = self.__loadMedPriceDS()
        self.assertTrue(compare(indicator.HT_TRENDLINE(ds, 252)[63], 88.257))
        self.assertTrue(compare(indicator.HT_TRENDLINE(ds, 252)[-3], 109.69))
        self.assertTrue(compare(indicator.HT_TRENDLINE(ds, 252)[-2], 110.18))
        self.assertTrue(compare(indicator.HT_TRENDLINE(ds, 252)[-1], 110.46))

    def testHT_TRENDMODE(self):
        ds = self.__loadMedPriceDS()
        self.assertTrue(compare(indicator.HT_TRENDMODE(ds, 252)[63], 1.0))

    def testKAMA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.KAMA(barDs.getCloseDataSeries(), 252, 10)[10], 92.6575))
        self.assertTrue(compare(indicator.KAMA(barDs.getCloseDataSeries(), 252, 10)[11], 92.7783))
        self.assertTrue(compare(indicator.KAMA(barDs.getCloseDataSeries(), 252, 10)[-1], 109.294))

    def testMA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MA(barDs.getCloseDataSeries(), 252, 2, talib.MA_Type.SMA)[1], 93.16))  # Original value 93.15
        self.assertTrue(compare(indicator.MA(barDs.getCloseDataSeries(), 252, 2, talib.MA_Type.SMA)[2], 94.59))
        self.assertTrue(compare(indicator.MA(barDs.getCloseDataSeries(), 252, 2, talib.MA_Type.SMA)[3], 94.73))
        self.assertTrue(compare(indicator.MA(barDs.getCloseDataSeries(), 252, 2, talib.MA_Type.SMA)[-1], 108.31))

    def testMACD(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MACD(barDs.getCloseDataSeries(), 252, 12, 26, 9)[0][33], -1.9738))
        self.assertTrue(compare(indicator.MACD(barDs.getCloseDataSeries(), 252, 12, 26, 9)[1][33], -2.7071))
        self.assertTrue(compare(indicator.MACD(barDs.getCloseDataSeries(), 252, 12, 26, 9)[2][33], (-1.9738)-(-2.7071)))
        self.assertTrue(compare(indicator.MACD(barDs.getCloseDataSeries(), 252, 26, 12, 9)[0][33], -1.9738))
        self.assertTrue(compare(indicator.MACD(barDs.getCloseDataSeries(), 252, 26, 12, 9)[1][33], -2.7071))
        self.assertTrue(compare(indicator.MACD(barDs.getCloseDataSeries(), 252, 26, 12, 9)[2][33], (-1.9738)-(-2.7071)))

    def testMACDEXT(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MACDEXT(barDs.getCloseDataSeries(), 252, 12, talib.MA_Type.EMA, 26, talib.MA_Type.EMA, 9, talib.MA_Type.EMA)[0][33], -1.9738))
        self.assertTrue(compare(indicator.MACDEXT(barDs.getCloseDataSeries(), 252, 12, talib.MA_Type.EMA, 26, talib.MA_Type.EMA, 9, talib.MA_Type.EMA)[1][33], -2.7071))
        self.assertTrue(compare(indicator.MACDEXT(barDs.getCloseDataSeries(), 252, 12, talib.MA_Type.EMA, 26, talib.MA_Type.EMA, 9, talib.MA_Type.EMA)[2][33], (-1.9738)-(-2.7071)))

    def testMAMA(self):
        ds = self.__loadMedPriceDS()
        self.assertTrue(compare(indicator.MAMA(ds, 252, 0.5, 0.05)[0][32], 85.3643))
        self.assertTrue(compare(indicator.MAMA(ds, 252, 0.5, 0.05)[0][-1], 110.1116))

    def testMAX(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MAX(barDs.getOpenDataSeries(), 252, 14)[13], 98.815))
        self.assertTrue(compare(indicator.MAX(barDs.getOpenDataSeries(), 252, 14)[14], 98.815))
        self.assertTrue(compare(indicator.MAX(barDs.getOpenDataSeries(), 252, 14)[-1], 110.69))

    def testMFI(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MFI(barDs, 252, 14)[14], 42.8923))
        self.assertTrue(compare(indicator.MFI(barDs, 252, 14)[15], 45.6072))
        self.assertTrue(compare(indicator.MFI(barDs, 252, 14)[-1], 53.1997))

    def testMIN(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MIN(barDs.getOpenDataSeries(), 252, 14)[13], 91.125))
        self.assertTrue(compare(indicator.MIN(barDs.getOpenDataSeries(), 252, 14)[14], 91.125))
        self.assertTrue(compare(indicator.MIN(barDs.getOpenDataSeries(), 252, 14)[-1], 107.75))

    def testMINUS_DI(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MINUS_DI(barDs, 252, 14)[14], 30.1684))
        self.assertTrue(compare(indicator.MINUS_DI(barDs, 252, 14)[28], 24.969182))
        self.assertTrue(compare(indicator.MINUS_DI(barDs, 252, 14)[-1], 21.1988))

    def testMINUS_DM(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MINUS_DM(barDs, 252, 14)[13], 12.995, 3))
        self.assertTrue(compare(indicator.MINUS_DM(barDs, 252, 14)[-2], 8.33))
        self.assertTrue(compare(indicator.MINUS_DM(barDs, 252, 14)[-1], 9.68))  # Original value 9.672

    def testMOM(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.MOM(barDs.getCloseDataSeries(), 252, 14)[14], -0.50))
        self.assertTrue(compare(indicator.MOM(barDs.getCloseDataSeries(), 252, 14)[15], -2.00))
        self.assertTrue(compare(indicator.MOM(barDs.getCloseDataSeries(), 252, 14)[16], -5.22))
        self.assertTrue(compare(indicator.MOM(barDs.getCloseDataSeries(), 252, 14)[-1], -1.13))

    def testNATR(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.NATR(barDs, 252, 14)[14], 3.9321))
        self.assertTrue(compare(indicator.NATR(barDs, 252, 14)[15], 3.7576))
        self.assertTrue(compare(indicator.NATR(barDs, 252, 14)[-1], 3.0229))

    def testPLUS_DI(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.PLUS_DI(barDs, 252, 14)[14], 20.3781))
        self.assertTrue(compare(indicator.PLUS_DI(barDs, 252, 14)[14+13], 22.1073))
        self.assertTrue(compare(indicator.PLUS_DI(barDs, 252, 14)[14+14], 20.3746))
        self.assertTrue(compare(indicator.PLUS_DI(barDs, 252, 14)[-1], 21.0000))

    def testPLUS_DM(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.PLUS_DM(barDs, 252, 14)[13], 10.28))
        self.assertTrue(compare(indicator.PLUS_DM(barDs, 252, 14)[-2], 10.317))
        self.assertTrue(compare(indicator.PLUS_DM(barDs, 252, 14)[-1], 9.59))  # Original value 9.58

    def testPPO(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.PPO(barDs.getCloseDataSeries(), 252, 2, 3, talib.MA_Type.SMA)[2], 1.10264))
        self.assertTrue(compare(indicator.PPO(barDs.getCloseDataSeries(), 252, 2, 3, talib.MA_Type.SMA)[3], -0.02813))
        self.assertTrue(compare(indicator.PPO(barDs.getCloseDataSeries(), 252, 2, 3, talib.MA_Type.SMA)[-1], -0.21191))

    def testROC(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ROC(barDs.getCloseDataSeries(), 252, 14)[14], -0.546))
        self.assertTrue(compare(indicator.ROC(barDs.getCloseDataSeries(), 252, 14)[15], -2.109))
        self.assertTrue(compare(indicator.ROC(barDs.getCloseDataSeries(), 252, 14)[16], -5.53))
        self.assertTrue(compare(indicator.ROC(barDs.getCloseDataSeries(), 252, 14)[-1], -1.0367))

    def testROCR(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ROCR(barDs.getCloseDataSeries(), 252, 14)[14], 0.994536, 4))
        self.assertTrue(compare(indicator.ROCR(barDs.getCloseDataSeries(), 252, 14)[15], 0.978906, 4))
        self.assertTrue(compare(indicator.ROCR(barDs.getCloseDataSeries(), 252, 14)[16], 0.944689, 4))
        self.assertTrue(compare(indicator.ROCR(barDs.getCloseDataSeries(), 252, 14)[-1], 0.989633, 4))

    def testROCR100(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ROCR100(barDs.getCloseDataSeries(), 252, 14)[14], 99.4536, 4))
        self.assertTrue(compare(indicator.ROCR100(barDs.getCloseDataSeries(), 252, 14)[15], 97.8906, 4))
        self.assertTrue(compare(indicator.ROCR100(barDs.getCloseDataSeries(), 252, 14)[16], 94.4689, 4))
        self.assertTrue(compare(indicator.ROCR100(barDs.getCloseDataSeries(), 252, 14)[-1], 98.9633, 4))

    def testRSI(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.RSI(barDs.getCloseDataSeries(), 252, 14)[14], 49.15))  # Original value 49.14
        self.assertTrue(compare(indicator.RSI(barDs.getCloseDataSeries(), 252, 14)[15], 52.33))  # Original value 52.32
        self.assertTrue(compare(indicator.RSI(barDs.getCloseDataSeries(), 252, 14)[16], 46.07))
        self.assertTrue(compare(indicator.RSI(barDs.getCloseDataSeries(), 252, 14)[-1], 49.63))

    def testSAR(self):
        barDs = self.__loadSarTestBarDs()
        self.assertTrue(compare(indicator.SAR(barDs, len(SAR_HIGH), 0.02, 0.20)[1], 50.00))
        self.assertTrue(compare(indicator.SAR(barDs, len(SAR_HIGH), 0.02, 0.20)[2], 50.047))
        self.assertTrue(compare(indicator.SAR(barDs, len(SAR_HIGH), 0.02, 0.20)[5], 50.182))
        self.assertTrue(compare(indicator.SAR(barDs, len(SAR_HIGH), 0.02, 0.20)[-2], 52.93))
        self.assertTrue(compare(indicator.SAR(barDs, len(SAR_HIGH), 0.02, 0.20)[-1], 50.00))

    def testSMA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.SMA(barDs.getCloseDataSeries(), 252, 2)[1], 93.16))  # Original value 93.15
        self.assertTrue(compare(indicator.SMA(barDs.getCloseDataSeries(), 252, 2)[2], 94.59))
        self.assertTrue(compare(indicator.SMA(barDs.getCloseDataSeries(), 252, 2)[3], 94.73))
        self.assertTrue(compare(indicator.SMA(barDs.getCloseDataSeries(), 252, 2)[-1], 108.31))

    def testSTDDEV(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.STDDEV(barDs.getCloseDataSeries(), 252, 5.0, 1)[4], 1.2856))
        self.assertTrue(compare(indicator.STDDEV(barDs.getCloseDataSeries(), 252, 5.0, 1)[5], 0.4462))
        self.assertTrue(compare(indicator.STDDEV(barDs.getCloseDataSeries(), 252, 5.0, 1)[-1], 0.7144))
        self.assertTrue(compare(indicator.STDDEV(barDs.getCloseDataSeries(), 252, 5.0, 1.5)[4], 1.9285))
        self.assertTrue(compare(indicator.STDDEV(barDs.getCloseDataSeries(), 252, 5.0, 1.5)[5], 0.66937))
        self.assertTrue(compare(indicator.STDDEV(barDs.getCloseDataSeries(), 252, 5.0, 1.5)[-1], 1.075))

    def testSTOCH(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.STOCH(barDs, 252, 5, 3, talib.MA_Type.SMA, 3, talib.MA_Type.SMA)[0][8], 24.0128))
        self.assertTrue(compare(indicator.STOCH(barDs, 252, 5, 3, talib.MA_Type.SMA, 3, talib.MA_Type.SMA)[1][8], 36.254))
        self.assertTrue(compare(indicator.STOCH(barDs, 252, 5, 3, talib.MA_Type.SMA, 4, talib.MA_Type.SMA)[0][-1], 30.194))
        self.assertTrue(compare(indicator.STOCH(barDs, 252, 5, 3, talib.MA_Type.SMA, 4, talib.MA_Type.SMA)[1][-1], 46.641))

    def testSTOCHRSI(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 14, 1, talib.MA_Type.SMA)[0][27], 94.156709))
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 14, 1, talib.MA_Type.SMA)[1][27], 94.156709))
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 14, 1, talib.MA_Type.SMA)[0][-1], 0))
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 14, 1, talib.MA_Type.SMA)[1][-1], 0))

        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 45, 1, talib.MA_Type.SMA)[0][58], 79.729186))
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 45, 1, talib.MA_Type.SMA)[1][58], 79.729186))
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 45, 1, talib.MA_Type.SMA)[0][-1], 48.1550743))
        self.assertTrue(compare(indicator.STOCHRSI(barDs.getCloseDataSeries(), 252, 14, 45, 1, talib.MA_Type.SMA)[1][-1], 48.1550743))

    def testT3(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.T3(barDs.getCloseDataSeries(), 252, 5, 0.7)[24],  85.73))
        self.assertTrue(compare(indicator.T3(barDs.getCloseDataSeries(), 252, 5, 0.7)[25],  84.37))
        self.assertTrue(compare(indicator.T3(barDs.getCloseDataSeries(), 252, 5, 0.7)[-2], 109.03))
        self.assertTrue(compare(indicator.T3(barDs.getCloseDataSeries(), 252, 5, 0.7)[-1], 108.88))

    def testTRANGE(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.TRANGE(barDs, 252)[1], 3.535, 3))
        self.assertTrue(compare(indicator.TRANGE(barDs, 252)[13], 9.685, 3))
        self.assertTrue(compare(indicator.TRANGE(barDs, 252)[41], 5.125, 3))
        self.assertTrue(compare(indicator.TRANGE(barDs, 252)[-1], 2.88))

    def testTRIMA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.TRIMA(barDs.getCloseDataSeries(), 252, 10)[9], 93.6043))
        self.assertTrue(compare(indicator.TRIMA(barDs.getCloseDataSeries(), 252, 10)[10], 93.4252))
        self.assertTrue(compare(indicator.TRIMA(barDs.getCloseDataSeries(), 252, 10)[-2], 109.1850, 3))
        self.assertTrue(compare(indicator.TRIMA(barDs.getCloseDataSeries(), 252, 10)[-1], 109.1407))

    def testTRIX(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.TRIX(barDs.getCloseDataSeries(), 252, 5)[13], 0.2589))
        self.assertTrue(compare(indicator.TRIX(barDs.getCloseDataSeries(), 252, 5)[14], 0.010495))
        self.assertTrue(compare(indicator.TRIX(barDs.getCloseDataSeries(), 252, 5)[-2], -0.058))
        self.assertTrue(compare(indicator.TRIX(barDs.getCloseDataSeries(), 252, 5)[-1], -0.095))

    def testULTOSC(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.ULTOSC(barDs, 252, 7, 14, 28)[28], 47.1713))
        self.assertTrue(compare(indicator.ULTOSC(barDs, 252, 7, 14, 28)[29], 46.2802))
        self.assertTrue(compare(indicator.ULTOSC(barDs, 252, 7, 14, 28)[-1], 40.0854))

    def testVAR(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.VAR(barDs.getCloseDataSeries(), 252, 5.0, 1)[4], 1.2856**2))
        self.assertTrue(compare(indicator.VAR(barDs.getCloseDataSeries(), 252, 5.0, 1)[5], 0.4462**2))
        self.assertTrue(compare(indicator.VAR(barDs.getCloseDataSeries(), 252, 5.0, 1)[-1], 0.7144**2))

    def testWILLR(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.WILLR(barDs, 252, 14)[13], -90.1943))
        self.assertTrue(compare(indicator.WILLR(barDs, 252, 14)[13+112], 0))

    def testWMA(self):
        barDs = self.__loadBarDS()
        self.assertTrue(compare(indicator.WMA(barDs.getCloseDataSeries(), 252, 2)[1], 93.71))
        self.assertTrue(compare(indicator.WMA(barDs.getCloseDataSeries(), 252, 2)[2], 94.52))
        self.assertTrue(compare(indicator.WMA(barDs.getCloseDataSeries(), 252, 2)[3], 94.86))  # Original value 94.85
        self.assertTrue(compare(indicator.WMA(barDs.getCloseDataSeries(), 252, 2)[-1], 108.16))
