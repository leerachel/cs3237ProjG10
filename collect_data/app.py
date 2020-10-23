from dotenv import load_dotenv
import os
import asyncio
import platform
from bleak import BleakClient

from cc2650 import LEDAndBuzzer, \
                   OpticalSensor, \
                   AccelerometerSensorMovementSensorMPU9250, \
                   GyroscopeSensorMovementSensorMPU9250, \
                   MagnetometerSensorMovementSensorMPU9250, \
                   MovementSensorMPU9250

from store import append_data_to_csv, read_data_from_csv

load_dotenv()


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
                append_data_to_csv("data.csv", final_dict)


            if command == "exit":
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
    
