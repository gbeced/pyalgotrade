# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

from optparse import OptionParser
import sys
import os
import tempfile
import hashlib
import subprocess

# Just in case pyalgotrade isn't installed.
uploadBarsPath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(uploadBarsPath, "..", ".."))

from pyalgotrade.barfeed import yahoofeed


def get_md5(value):
    m = hashlib.md5()
    m.update(value)
    return m.hexdigest()


def datetimeToCSV(dateTime):
    return dateTime.strftime("%Y-%m-%dT%H:%M:%S")


def parse_cmdline():
    usage = "usage: %prog [options] csv1 csv2 ..."
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--instrument", dest="instrument", help="Mandatory. The instrument's symbol. Note that all csv files must belong to the same instrument.")
    parser.add_option("-u", "--url", dest="url", help="The location of the remote_api endpoint. Example: http://YOURAPPID.appspot.com/remote_api")
    parser.add_option("-c", "--appcfg_path", dest="appcfg_path", help="Path where appcfg.py resides")
    mandatory_options = [
        "instrument",
        "url",
        ]

    (options, args) = parser.parse_args()

    # Check that all mandatory options are available.
    for opt in mandatory_options:
        if getattr(options, opt) is None:
            raise Exception("--%s option is missing" % opt)

    if len(args) == 0:
        raise Exception("No csv files to upload")

    return (options, args)


def gen_bar_key(instrument, barType, bar):
    return get_md5("%s %d %s" % (instrument, barType, bar.getDateTime()))


def write_intermediate_csv(instrument, csvFiles, csvToUpload):
    csvToUpload.write("key,instrument,barType,dateTime,open_,close_,high,low,volume,adjClose\n")

    instrument = instrument.upper()
    barType = 1

    feed = yahoofeed.Feed()
    for csvFile in csvFiles:
        print "Loading bars from %s" % csvFile
        feed.addBarsFromCSV(instrument, csvFile)

    print "Writing intermediate csv into %s" % csvToUpload.name
    for dateTime, bars in feed:
        bar = bars[instrument]
        csvToUpload.write("%s,%s,%d,%s,%s,%s,%s,%s,%s,%s\n" % (
            gen_bar_key(instrument, barType, bar),
            instrument,
            barType,
            datetimeToCSV(bar.getDateTime()),
            bar.getOpen(),
            bar.getClose(),
            bar.getHigh(),
            bar.getLow(),
            bar.getVolume(),
            bar.getAdjClose()
            ))
    csvToUpload.flush()


def upload_intermediate_csv(options, csvPath):
    print "Uploading %s" % csvPath
    cmd = []
    if options.appcfg_path:
        cmd.append(os.path.join(options.appcfg_path, "appcfg.py"))
    else:
        cmd.append("appcfg.py")
    cmd.append("upload_data")
    cmd.append("--kind=Bar")
    cmd.append("--filename=%s" % csvPath)
    cmd.append("--config_file=%s" % os.path.join(uploadBarsPath, "bulkloader.yaml"))
    cmd.append("--url=%s" % options.url)
    cmd.append("--num_threads=1")

    popenObj = subprocess.Popen(args=cmd)
    popenObj.communicate()


def main():
    try:
        (options, args) = parse_cmdline()
        csvToUpload = tempfile.NamedTemporaryFile()
        write_intermediate_csv(options.instrument, args, csvToUpload)
        upload_intermediate_csv(options, csvToUpload.name)
    except Exception, e:
        sys.stdout.write("Error: %s\n" % e)
        sys.exit(1)


if __name__ == "__main__":
    main()
