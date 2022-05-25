import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import random

class InfluxdbService:
    def __init__(self, influxdb_config, debug):
        self.influxdb_config=influxdb_config
        self.debug=debug

    # Make write request to influxdb
    def writeDataBySystemCode(self, data_to_send, timestamp=0, measurement="STM"):
        # set timestamp value if not defined
        if timestamp == 0:
            timestamp = int(time.time()) * 1000
        # configure influxdb client API
        write_api = self.getInfluxdbClientApi()
        # prepare points
        points = []
        for system_code, data in data_to_send.items():
            point = self.prebuildPoint(system_code, timestamp, measurement)
            # add fields and values
            for key, value in data.items():
                point.field(key, value)
                # mock data in debug mode
                if self.debug:
                    if key == "temperature":
                        point.field(key, random.uniform(26, 27) // 0.01 / 100)
                    elif key == "humidity":
                        point.field(key, int(random.uniform(30, 35)))
            points.append(point)
        # send request to influxdb
        write_api.write(bucket=self.influxdb_config['bucket'], record=points)

    def prebuildPoint(self, system_code, date, measurement):
        return influxdb_client.Point(measurement).tag("system_code", system_code) \
            .time(time=date, write_precision="ms")

    def getInfluxdbClientApi(self):
        return influxdb_client.InfluxDBClient(
            url=self.influxdb_config['protocol'] + '://' + self.influxdb_config['host'],
            token=self.influxdb_config['token'],
            org=self.influxdb_config['org']
        ).write_api(write_options=SYNCHRONOUS)
