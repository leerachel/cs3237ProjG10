import csv
import json

from cc2650 import OpticalSensor, \
                   MovementSensorMPU9250

import os.path

FIELD_NAMES = [OpticalSensor.LIGHT_LABEL,
               MovementSensorMPU9250.ACCEL_LABEL,
               MovementSensorMPU9250.MAG_LABEL,
               MovementSensorMPU9250.GYRO_LABEL]


def append_data_to_csv(file_path, data):
    file_exists = os.path.isfile(file_path)
    with open(file_path, "a", newline="") as csv_file:

        csv_writer = csv.DictWriter(csv_file, delimiter=',', fieldnames=FIELD_NAMES)
        if not file_exists:
            csv_writer.writeheader()
        csv_writer.writerow({
            OpticalSensor.LIGHT_LABEL: json.dumps(data[OpticalSensor.LIGHT_LABEL]),
            MovementSensorMPU9250.ACCEL_LABEL: json.dumps(data[MovementSensorMPU9250.ACCEL_LABEL]),
            MovementSensorMPU9250.MAG_LABEL: json.dumps(data[MovementSensorMPU9250.MAG_LABEL]),
            MovementSensorMPU9250.GYRO_LABEL: json.dumps(data[MovementSensorMPU9250.GYRO_LABEL])
        })


def read_data_from_csv(file_path):
    with open(file_path, "r", newline="") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data = []
        for row in csv_reader:
            data.append(row)

        return data






