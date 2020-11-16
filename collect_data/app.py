from dotenv import load_dotenv
import os
import asyncio
import platform
from bleak import BleakClient
import paho.mqtt.client as mqtt
import json

from cc2650 import LEDAndBuzzer, \
                   OpticalSensor, \
                   AccelerometerSensorMovementSensorMPU9250, \
                   GyroscopeSensorMovementSensorMPU9250, \
                   MagnetometerSensorMovementSensorMPU9250, \
                   MovementSensorMPU9250

from store import append_data_to_csv, read_data_from_csv, \
                insert_light_data_into_cloud_DB, insert_acc_data_into_cloud_DB, \
                insert_mag_data_into_cloud_DB, insert_gyro_data_into_cloud_DB

# Define Variables
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "helloTopic"
MQTT_MSG = ""

load_dotenv()

# Define on_publish event function
def on_publish(client, userdata, mid):
    print("Message Published...")

# Initiate MQTT Client
mqttc = mqtt.Client()

# Register publish callback function
mqttc.on_publish = on_publish

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 

async def start_sensor(address):
    async with BleakClient(address) as client:
        x = await client.is_connected()
        print("Connected: {0}".format(x))

        light_sensor = OpticalSensor()
        acc_sensor = AccelerometerSensorMovementSensorMPU9250()
        gyro_sensor = GyroscopeSensorMovementSensorMPU9250()
        magneto_sensor = MagnetometerSensorMovementSensorMPU9250()
        movement_sensor = MovementSensorMPU9250()
        movement_sensor.register(acc_sensor)
        movement_sensor.register(gyro_sensor)
        movement_sensor.register(magneto_sensor)
        led_and_buzzer = LEDAndBuzzer()

        await led_and_buzzer.enable_config(client)
        print("Wait for LED lights to stop flashing before entering commands...")

        while True:
            command = input("Enter command:")
            if command == "start":
                print("Starting sensors...")
                cntr = 0
                await led_and_buzzer.notify(client, 0x04) # buzzer only
                await movement_sensor.start_listener(client)
                await light_sensor.start_listener(client)
                while cntr < 5:
                    await asyncio.sleep(1.0)
                    print(f"Started reading for {cntr+1} second(s)")
                    cntr += 1

                light_dict = await light_sensor.stop_sensor(client)
                final_dict = await movement_sensor.stop_sensor(client)
                final_dict[OpticalSensor.LIGHT_LABEL] = light_dict
                await led_and_buzzer.notify(client, 0x00)
                output = input("Is it a score? (y/n/o)")
                if output=="y":
                    score = 1
                elif output=="n":
                    score = 0
                elif output=="o":
                    score = -1
                else:
                    score = -1
                final_dict["score"] = score
                append_data_to_csv("data.csv", final_dict)
                MQTT_MSG = json.dumps(final_dict)
                mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) # Connect with MQTT Broker
                mqttc.publish(MQTT_TOPIC,MQTT_MSG) # Publish message to MQTT Broker                          
                mqttc.disconnect() # Disconnect from MQTT_Broker
                #insert_light_data_into_cloud_DB(final_dict)
                #insert_acc_data_into_cloud_DB(final_dict)
                #insert_mag_data_into_cloud_DB(final_dict)
                #insert_gyro_data_into_cloud_DB(final_dict)

            if command == "exit":
                MQTT_MSG = "lastshot"
                mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) # Connect with MQTT Broker
                mqttc.publish(MQTT_TOPIC,MQTT_MSG) # Publish message to MQTT Broker                          
                mqttc.disconnect() # Disconnect from MQTT_Broker
                return


if __name__ == "__main__":
    """
    To find the address, once your sensor tag is blinking the green led after pressing the button, run the discover.py
    file which was provided as an example from bleak to identify the sensor tag device
    """


    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    address = (
        os.environ.get('DEVICE_ADDRESS')
        if platform.system() != "Darwin"
        else "6FFBA6AE-0802-4D92-B1CD-041BE4B4FEB9"
    )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_sensor(address))
    loop.close()
    
