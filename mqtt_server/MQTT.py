# Import package
import paho.mqtt.client as mqtt
import pymongo
import socket
import sys
import datetime
import json
import ast
from pymongo import MongoClient

# MONGODB
client = MongoClient('mongodb://localhost:27017/')

with client:
    # Connects to db -> sensorDB
    db = client.sensorDB

# Define Variables
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = "helloTopic"
MQTT_MSG = "hello MQTT"

# Define on connect event function
# We shall subscribe to our Topic in this function
def on_connect(self, mosq, obj, rc):
    self.subscribe(MQTT_TOPIC, 0)
    print("Connected...")

# Define on_message event function. 
# This function will be invoked every time,
# a new message arrives for the subscribed topic 
def on_message(mosq, obj, msg):
    rawData = msg.payload.decode('utf-8')
    
    # Read move number
    f=open("moveCount.txt", "r")
    if f.mode == 'r':
        contents = f.read()
        print(contents)
        moveNum = int(float(contents)) + 1
        f.close()

    # Getting session count from previous saved sessionNum
    f=open("sessionCount.txt", "r")
    if f.mode == 'r':
        contents = f.read()
        print(contents)
        session = int(float(contents)) + 1
        f.close()

    # Read last data
    with open('data.txt') as json_file:
        myDict = json.load(json_file)

    #print("Payload: " + rawData)
    # if incoming message is the last shot of the session
    if (rawData=="lastshot"):
        print(rawData)
        # Insert end flag
        rawDataStream = {
            'session': session, 'moveNum': moveNum, 
            'AccXD1':float(0), 'AccYD1':float(0), 'AccZD1':float(0), 
            'GyroXD1':float(0), 'GyroYD1':float(0), 'GyroZD1':float(0), 
            'isEndSession': bool("true"), 'timeStamp':myDict['accelerometer'][str(len(myDict['light'])-1)][3]
        }
        db.individualCollection.insert_one(rawDataStream)
        # Reset moveNum to 0
        f=open("moveCount.txt", "w")
        if f.mode == 'w':
            f.write(str(0))
            f.close()
        # Write Session Number
        f=open("sessionCount.txt", "w")
        if f.mode == 'w':
            f.write(str(session))
            f.close()
    else:
        # Dump json here, and read json again
        with open('data.txt', 'w') as outfile:
            outfile.write(rawData)
        with open('data.txt') as json_file:
            myDict = json.load(json_file)
            print("score:", myDict['score'])
            print("light:", len(myDict['light']))
            print("light:", myDict['light']['0'])
        
        # Raw data insertion
        for j in range(len(myDict['light'])):
            #if (i==len(accelerometer_master_list)-1):
                #flag = bool("true")
            #else:
            flag = bool("")
            i = str(j)
            rawDataStream = {
                'session': session, 'moveNum': moveNum, 
                'AccXD1':float(myDict['accelerometer'][i][0]), 'AccYD1':float(myDict['accelerometer'][i][1]), 'AccZD1':float(myDict['accelerometer'][i][2]), 
                'GyroXD1':float(myDict['gyroscope'][i][0]), 'GyroYD1':float(myDict['gyroscope'][i][1]), 'GyroZD1':float(myDict['gyroscope'][i][2]), 
                'isEndSession': flag, 'timeStamp':myDict['accelerometer'][i][3]
            }
            db.individualCollection.insert_one(rawDataStream)

        # ML score insertion
        if (int(myDict['score'])==1):
            score = "hit"
        elif (int(myDict['score'])==0):
            score = "miss"
        else:
            score = "invalid"
        MLdatastream = {
            'session': session, 'moveNum': moveNum, 
            'predictedMoveD1': score,
            'timeStamp':myDict['accelerometer'][i][3]
        }
        db.checkerCollection.insert_one(MLdatastream)
    
        # Write moveNum
        f=open("moveCount.txt", "w")
        if f.mode == 'w':
            f.write(str(moveNum))
            f.close()


    

def on_subscribe(mosq, obj, mid, granted_qos):
    print("Subscribed to Topic: " + 
	MQTT_MSG + " with QoS: " + str(granted_qos))

# Initiate MQTT Client
mqttc = mqtt.Client()

# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

# Continue monitoring the incoming messages for subscribed topic
mqttc.loop_forever()