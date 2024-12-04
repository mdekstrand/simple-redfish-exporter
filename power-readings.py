#!/usr/bin/python3

import sys
import os
import time
import csv
import warnings
import select

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# IKVM access information
# access credentials are in ~/.netrc
IKVM_HOST="192.168.1.202"
# polling interval in seconds
POLL_INTERVAL=0.2

# non-blocking stdin, we want for it to close to quit
os.set_blocking(sys.stdin.fileno(), False)

warnings.simplefilter('ignore', InsecureRequestWarning)

def check_finished():
    global finished
    rd, _w, _x = select.select([sys.stdin], [], [], POLL_INTERVAL)
    if rd:
        data = os.read(sys.stdin.fileno(), 8)
        if not data:
            finished = True

sys.stdout.reconfigure(line_buffering=True)
finished = False
wrote_header = False
while True:
    pt = time.perf_counter()
    r = requests.get(f'https://{IKVM_HOST}/redfish/v1/Chassis/Self/Power', verify=False)
    data = r.json()
    psus = data.get('PowerSupplies', None)
    if not psus:
        print('no power supplies available', file=sys.stderr)
        sys.exit(2)

    if not wrote_header:
        cols = ['Time']
        for i in range(len(psus)):
            cols += [f'PSU{i}InputWatts', f'PSU{i}OutputWatts']
        cols += ['TotalWatts', 'OutputWatts']
        print(','.join(cols))
        wrote_header = True

    row = [pt]
    tot_in = 0.0
    tot_out = 0.0
    for psu in psus:
        in_w = psu.get('PowerInputWatts', None)
        if in_w is not None:
            tot_in += in_w
        out_w = psu.get('PowerOutputWatts', None)
        if out_w is not None:
            tot_out += out_w
        row += [in_w, out_w]
    row += [tot_in, tot_out]
    print(','.join([str(x) for x in row]))

    # if we are finished, we want one more pass for the last data
    if finished:
        break
    else:
        check_finished()
