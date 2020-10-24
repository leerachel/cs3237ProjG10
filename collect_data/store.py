import csv
import json
import boto3
from decimal import Decimal

# Get the service resource.
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SensorData')
#print(table.creation_date_time)

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


def insert_light_data_into_cloud_DB(data):
    for idx in data[OpticalSensor.LIGHT_LABEL]:
        table.put_item(Item={
                    'SensorId': OpticalSensor.LIGHT_LABEL,
                    'Timestamp': data[OpticalSensor.LIGHT_LABEL][idx][1],
                    'Value': Decimal(str(data[OpticalSensor.LIGHT_LABEL][idx][0])),
                    })

def insert_acc_data_into_cloud_DB(data):
    for idx in data[MovementSensorMPU9250.ACCEL_LABEL]:
        table.put_item(Item={
                    'SensorId': MovementSensorMPU9250.ACCEL_LABEL,
                    'Timestamp': data[MovementSensorMPU9250.ACCEL_LABEL][idx][3],
                    'Value': {
                        'acc_X': Decimal(str(data[MovementSensorMPU9250.ACCEL_LABEL][idx][0])),
                        'acc_Y': Decimal(str(data[MovementSensorMPU9250.ACCEL_LABEL][idx][1])),
                        'acc_Z': Decimal(str(data[MovementSensorMPU9250.ACCEL_LABEL][idx][2]))
                        }
                    })

def insert_mag_data_into_cloud_DB(data):
    for idx in data[MovementSensorMPU9250.MAG_LABEL]:
        table.put_item(Item={
                    'SensorId': MovementSensorMPU9250.MAG_LABEL,
                    'Timestamp': data[MovementSensorMPU9250.MAG_LABEL][idx][3],
                    'Value': {
                        'mag_x': Decimal(str(data[MovementSensorMPU9250.MAG_LABEL][idx][0])),
                        'mag_Y': Decimal(str(data[MovementSensorMPU9250.MAG_LABEL][idx][1])),
                        'mag_Z': Decimal(str(data[MovementSensorMPU9250.MAG_LABEL][idx][2])),
                        }
                    })

def insert_gyro_data_into_cloud_DB(data):
    for idx in data[MovementSensorMPU9250.GYRO_LABEL]:
        table.put_item(Item={
                    'SensorId': MovementSensorMPU9250.GYRO_LABEL,
                    'Timestamp': data[MovementSensorMPU9250.GYRO_LABEL][idx][3],
                    'Value': { 
                        'gyro_X': Decimal(str(data[MovementSensorMPU9250.GYRO_LABEL][idx][0])),
                        'gyro_Y': Decimal(str(data[MovementSensorMPU9250.GYRO_LABEL][idx][1])),
                        'gyro_Z': Decimal(str(data[MovementSensorMPU9250.GYRO_LABEL][idx][2])),
                        }
                    })