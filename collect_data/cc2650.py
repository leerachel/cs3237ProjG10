# -*- coding: utf-8 -*-
"""
TI CC2650 SensorTag
-------------------

Adapted by Ashwin from the following sources:
 - https://github.com/IanHarvey/bluepy/blob/a7f5db1a31dba50f77454e036b5ee05c3b7e2d6e/bluepy/sensortag.py
 - https://github.com/hbldh/bleak/blob/develop/examples/sensortag.py

"""
import asyncio
import platform
import struct
import datetime

from bleak import BleakClient

sensorPeriod = bytearray([0x0A]) #10Hz only implemented for Movement Sensor and Optical Sensor

class Service:
    """
    Here is a good documentation about the concepts in ble;
    https://learn.adafruit.com/introduction-to-bluetooth-low-energy/gatt

    In TI SensorTag there is a control characteristic and a data characteristic which define a service or sensor
    like the Light Sensor, Humidity Sensor etc

    Please take a look at the official TI user guide as well at
    https://processors.wiki.ti.com/index.php/CC2650_SensorTag_User's_Guide
    """

    def __init__(self):
        self.read_count = 0  # Tracks number of reads
        self.dict = {} # dict storing time to reading mapping
        self.data_uuid = None
        self.ctrl_uuid = None
        self.period_uuid = None



class Sensor(Service):

    def callback(self, sender: int, data: bytearray):
        raise NotImplementedError()

    async def start_listener(self, client, *args):
        self.read_count = 0
        self.dict = {}
        # start the sensor on the device
        if self.ctrl_uuid:
            write_value = bytearray([0x01])
            await client.write_gatt_char(self.ctrl_uuid, write_value)
        if self.period_uuid:
            await client.write_gatt_char(self.period_uuid, sensorPeriod)
        # listen using the handler
        await client.start_notify(self.data_uuid, self.callback)

    async def stop_sensor(self, client):
        # stop the sensor on the device
        write_value = bytearray([0x00])
        await client.write_gatt_char(self.ctrl_uuid, write_value)
        return self.dict


class MovementSensorMPU9250SubService:

    def __init__(self):
        self.bits = 0

    def enable_bits(self):
        return self.bits

    def cb_sensor(self, data):
        raise NotImplementedError


class BatteryService(Service):
    def __init__(self):
        super().__init__()
        self.data_uuid = "00002a19-0000-1000-8000-00805f9b34fb"
    

    async def read(self, client):
        '''Returns the battery level in percent'''
        battery_level = await client.read_gatt_char(self.data_uuid)
        print("Battery Level: {0}%".format(int(battery_level[0])))


class MovementSensorMPU9250(Sensor):
    GYRO_XYZ = 7
    ACCEL_XYZ = 7 << 3
    MAG_XYZ = 1 << 6
    ACCEL_RANGE_2G  = 0 << 8
    ACCEL_RANGE_4G  = 1 << 8
    ACCEL_RANGE_8G  = 2 << 8
    ACCEL_RANGE_16G = 3 << 8
    ACCEL_LABEL = "accelerometer"
    MAG_LABEL = "magnetometer"
    GYRO_LABEL = "gyroscope"

    def __init__(self):
        super().__init__()
        self.data_uuid = "f000aa81-0451-4000-b000-000000000000"
        self.ctrl_uuid = "f000aa82-0451-4000-b000-000000000000"
        self.period_uuid = "f000aa83-0451-4000-b000-000000000000"

        self.ctrlBits = 0

        self.sub_callbacks = []

    def register(self, cls_obj: MovementSensorMPU9250SubService):
        self.ctrlBits |= cls_obj.enable_bits()
        self.sub_callbacks.append(cls_obj.cb_sensor)

    async def start_listener(self, client, *args):
        # start the sensor on the device
        self.read_count = 0
        self.dict = { MovementSensorMPU9250.ACCEL_LABEL: {},
                      MovementSensorMPU9250.MAG_LABEL: {},
                      MovementSensorMPU9250.GYRO_LABEL:{}}
        await client.write_gatt_char(self.ctrl_uuid, bytearray(struct.pack("<H", self.ctrlBits)))
        await client.write_gatt_char(self.period_uuid, sensorPeriod)

        # listen using the handler
        await client.start_notify(self.data_uuid, self.callback)

    async def stop_sensor(self, client):
        # stop the sensor on the device
        await client.write_gatt_char(self.ctrl_uuid, bytearray(b'\x00\x00'))

        return self.dict

    def callback(self, sender: int, data: bytearray):
        unpacked_data = struct.unpack("<hhhhhhhhh", data)
        for cb in self.sub_callbacks:
            cb(unpacked_data, self.dict, self.read_count)

        self.read_count += 1


class AccelerometerSensorMovementSensorMPU9250(MovementSensorMPU9250SubService):
    def __init__(self):
        super().__init__()
        self.bits = MovementSensorMPU9250.ACCEL_XYZ | MovementSensorMPU9250.ACCEL_RANGE_4G
        self.scale = 8.0/32768.0 # TODO: why not 4.0, as documented? @Ashwin Need to verify

    def cb_sensor(self, data, dict, read_count):
        '''Returns (x_accel, y_accel, z_accel) in units of g'''
        rawVals = data[3:6]
        dict[MovementSensorMPU9250.ACCEL_LABEL][read_count] = tuple([ v*self.scale for v in rawVals ]+[datetime.datetime.now().isoformat()])
        print("[MovementSensor] Accelerometer:", tuple([ v*self.scale for v in rawVals ]))


class MagnetometerSensorMovementSensorMPU9250(MovementSensorMPU9250SubService):
    def __init__(self):
        super().__init__()
        self.bits = MovementSensorMPU9250.MAG_XYZ
        self.scale = 4912.0 / 32760
        # Reference: MPU-9250 register map v1.4

    def cb_sensor(self, data, dict, read_count):
        '''Returns (x_mag, y_mag, z_mag) in units of uT'''
        rawVals = data[6:9]
        dict[MovementSensorMPU9250.MAG_LABEL][read_count] = tuple([ v*self.scale for v in rawVals ]+[datetime.datetime.now().isoformat()])
        print("[MovementSensor] Magnetometer:", tuple([ v*self.scale for v in rawVals ]))


class GyroscopeSensorMovementSensorMPU9250(MovementSensorMPU9250SubService):
    def __init__(self):
        super().__init__()
        self.bits = MovementSensorMPU9250.GYRO_XYZ
        self.scale = 500.0/65536.0

    def cb_sensor(self, data, dict, read_count):
        '''Returns (x_gyro, y_gyro, z_gyro) in units of degrees/sec'''
        rawVals = data[0:3]
        dict[MovementSensorMPU9250.GYRO_LABEL][read_count] = tuple([ v*self.scale for v in rawVals ]+[datetime.datetime.now().isoformat()])
        print("[MovementSensor] Gyroscope:", tuple([ v*self.scale for v in rawVals ]))


class OpticalSensor(Sensor):
    LIGHT_LABEL = "light"
    def __init__(self):
        super().__init__()
        self.data_uuid = "f000aa71-0451-4000-b000-000000000000"
        self.ctrl_uuid = "f000aa72-0451-4000-b000-000000000000"
        self.period_uuid = "f000aa73-0451-4000-b000-000000000000"

    def callback(self, sender: int, data: bytearray):
        raw = struct.unpack('<h', data)[0]
        m = raw & 0xFFF
        e = (raw & 0xF000) >> 12
        reading = 0.01 * (m << e)
        self.dict[self.read_count] = tuple([reading, datetime.datetime.now().isoformat()])
        self.read_count += 1
        print("[OpticalSensor] Reading from light sensor:", reading)


class HumiditySensor(Sensor):
    def __init__(self):
        super().__init__()
        self.data_uuid = "f000aa21-0451-4000-b000-000000000000"
        self.ctrl_uuid = "f000aa22-0451-4000-b000-000000000000"

    def callback(self, sender: int, data: bytearray):
        (rawT, rawH) = struct.unpack('<HH', data)
        temp = -40.0 + 165.0 * (rawT / 65536.0)
        RH = 100.0 * (rawH/65536.0)
        print(f"[HumiditySensor] Ambient temp: {temp}; Relative Humidity: {RH}")


class BarometerSensor(Sensor):
    def __init__(self):
        super().__init__()
        self.data_uuid = "f000aa41-0451-4000-b000-000000000000"
        self.ctrl_uuid = "f000aa42-0451-4000-b000-000000000000"

    def callback(self, sender: int, data: bytearray):
        (tL, tM, tH, pL, pM, pH) = struct.unpack('<BBBBBB', data)
        temp = (tH*65536 + tM*256 + tL) / 100.0
        press = (pH*65536 + pM*256 + pL) / 100.0
        print(f"[BarometerSensor] Ambient temp: {temp}; Pressure Millibars: {press}")


class LEDAndBuzzer(Service):
    """
        Adapted from various sources. Src: https://evothings.com/forum/viewtopic.php?t=1514 and the original TI spec
        from https://processors.wiki.ti.com/index.php/CC2650_SensorTag_User's_Guide#Activating_IO

        Codes:
            1 = red
            2 = green
            3 = red + green
            4 = buzzer
            5 = red + buzzer
            6 = green + buzzer
            7 = all
    """

    def __init__(self):
        super().__init__()
        self.data_uuid = "f000aa65-0451-4000-b000-000000000000"
        self.ctrl_uuid = "f000aa66-0451-4000-b000-000000000000"

    async def enable_config(self, client):
        # enable the config
        write_value = bytearray([0x01])
        await client.write_gatt_char(self.ctrl_uuid, write_value)
        await client.write_gatt_char(self.data_uuid, bytearray([0x00]))  # off buzzer once config done

    async def notify(self, client, code):
        # turn on the red led as stated from the list above using 0x01
        write_value = bytearray([code])
        await client.write_gatt_char(self.data_uuid, write_value)


async def run(address):
    async with BleakClient(address) as client:
        x = await client.is_connected()
        print("Connected: {0}".format(x))

        led_and_buzzer = LEDAndBuzzer()

        light_sensor = OpticalSensor()
        await light_sensor.start_listener(client)

        # humidity_sensor = HumiditySensor()
        # await humidity_sensor.start_listener(client)

        # barometer_sensor = BarometerSensor()
        # await barometer_sensor.start_listener(client)

        acc_sensor = AccelerometerSensorMovementSensorMPU9250()
        gyro_sensor = GyroscopeSensorMovementSensorMPU9250()
        magneto_sensor = MagnetometerSensorMovementSensorMPU9250()

        movement_sensor = MovementSensorMPU9250()
        movement_sensor.register(acc_sensor)
        movement_sensor.register(gyro_sensor)
        movement_sensor.register(magneto_sensor)
        await movement_sensor.start_listener(client)

        while True:
            # we don't want to exit the "with" block initiating the client object as the connection is disconnected
            # unless the object is stored
            await asyncio.sleep(1.0)


