# pyright: basic
import sys
import os
import io
import time
import csv
from typing import Any
import warnings
import select
from dataclasses import dataclass, field, fields

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning # type: ignore

from flask import Flask

from models import PowerData

IKVM_HOST = os.environ["IKVM_HOST"]

app = Flask(__name__)
warnings.simplefilter('ignore', InsecureRequestWarning)

@dataclass
class Metric:
    help: str
    type: str = 'gauge'
    values: list[tuple[str, float]] = field(default_factory=list)

@dataclass
class Measurement:
    redfish_psu_present: Metric = field(default_factory=lambda: Metric('Whether the PSU is active'))
    redfish_psu_input_power: Metric = field(default_factory=lambda: Metric('Instantaneous output power (watts)'))
    redfish_psu_line_voltage: Metric = field(default_factory=lambda: Metric('Current line input voltage'))
    redfish_psu_output_power: Metric = field(default_factory=lambda: Metric('Instantaneous output power (watts)'))
    redfish_psu_output_voltage: Metric = field(default_factory=lambda: Metric('Current output voltage'))
    redfish_psu_temperature: Metric = field(default_factory=lambda: Metric('Power supply temperature'))

@app.route("/metrics")
def metrics():
    r = requests.get(f'https://{IKVM_HOST}/redfish/v1/Chassis/Self/Power', verify=False)

    data = r.json()
    data = PowerData.model_validate(data)
    if not data.PowerSupplies:
        app.logger.warning('no power supplies available')

    metrics = Measurement()

    for psu in data.PowerSupplies:
        key = f'psu_id="{psu.MemberId}",name="{psu.Name}"'
        if psu.Status.State != 'Present':
            metrics.redfish_psu_present.values.append((key, 0))
            continue

        metrics.redfish_psu_present.values.append((key, 1))
        metrics.redfish_psu_line_voltage.values.append((key, psu.LineInputVoltage))
        metrics.redfish_psu_input_power.values.append((key, psu.PowerInputWatts))
        metrics.redfish_psu_output_power.values.append((key, psu.PowerOutputWatts))
        metrics.redfish_psu_output_voltage.values.append((key, psu.PowerOutputVoltage))
        metrics.redfish_psu_temperature.values.append((key, psu.PowerTemperature))

    out = io.StringIO()
    for f in fields(metrics):
        metric: Metric = getattr(metrics, f.name)
        print(f'# HELP {f.name} {metric.help}', file=out)
        print(f'# TYPE {f.name} {metric.type}', file=out)
        for key, val in metric.values:
            print('%s{%s} %s' % (f.name, key, val), file=out)

    return out.getvalue()
