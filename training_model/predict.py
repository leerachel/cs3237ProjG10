import os
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
#import seaborn as sns
import copy
import json
import pprint

from datetime import datetime, timedelta
from pandas import DataFrame
from keras.models import Sequential
from keras.layers import LSTM, Bidirectional
from keras.layers.core import Dense, Dropout
from keras.optimizers import SGD
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
import tensorflow as tf

model = tf.keras.models.load_model('myModel.h5')
model.summary()

#in this file, there should only be data on one throw. 
df = pd.read_csv('data.csv')

#============== here on forth, i just copied from the collab==========================
print(df.shape) # (totalNumberOfShots, metrics)
totalNumberOfShots = df.shape[0]
df.isnull().any()

lightList = []
accelerometerList = []
gyroscopeList = []
score_master_list = [] # does not need further data organization

for shotIdx in range(totalNumberOfShots):
    lightList.append(json.loads(df.loc[shotIdx]['light']))
    accelerometerList.append(json.loads(df.loc[shotIdx]['accelerometer']))
    gyroscopeList.append(json.loads(df.loc[shotIdx]['gyroscope']))
    score_master_list.append(df.loc[shotIdx]['score'])

if (len(lightList)==len(accelerometerList)==len(gyroscopeList)==len(score_master_list)==totalNumberOfShots):
    print("Correct number of shots across all lists: %d" % totalNumberOfShots)
else:
    print("WARNING: CHECK CSV FILE!!!")
    
    

light_master_list = []
accelerometer_master_list = []
gyroscope_master_list = []

for shotIdx in range(totalNumberOfShots):
    data_entries_list = ([(key, value) for key, value in lightList[shotIdx].items()]) # Stored as a tuple (#, [reading, timestamp])
    light_master_list.append(data_entries_list)

    data_entries_list = ([(key, value) for key, value in accelerometerList[shotIdx].items()]) # Stored as a tuple (#, [X,Y,Z, timestamp])
    accelerometer_master_list.append(data_entries_list)

    data_entries_list = ([(key, value) for key, value in gyroscopeList[shotIdx].items()]) # Stored as a tuple (#, [X,Y,Z, timestamp])
    gyroscope_master_list.append(data_entries_list)
    
    
TUPLE_DATA_POSITION = 1
LIGHT_DATA_POSITION = 0
LIGHT_TIMESTAMP_POSITION = 1
ACC_X_POSITION = 0
ACC_Y_POSITION = 1
ACC_Z_POSITION = 2
ACC_TIMESTAMP_POSITION = 3
GYRO_X_POSITION = 0
GYRO_Y_POSITION = 1
GYRO_Z_POSITION = 2
GYRO_TIMESTAMP_POSITION = 3

light_per_shot_arr = []
acc_per_shot_arr = []
gyro_per_shot_arr = []

for shotIdx in range(totalNumberOfShots):
    light_timestamp_dict = {'timestamp': [], 'reading': []}
    accelerometer_timestamp_dict = {'timestamp': [], 'X': [], 'Y': [], 'Z': []}
    gyroscope_timestamp_dict = {'timestamp': [], 'X': [], 'Y': [], 'Z': []}

    # LIGHT
    for dataPointIdx in range(len(light_master_list[shotIdx])):
        light_timestamp_dict['timestamp'].append(light_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][LIGHT_TIMESTAMP_POSITION])
        light_timestamp_dict['reading'].append(light_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][LIGHT_DATA_POSITION])
    light_per_shot_arr.append(light_timestamp_dict)

    # ACC
    for dataPointIdx in range(len(accelerometer_master_list[shotIdx])):
        accelerometer_timestamp_dict['timestamp'].append(accelerometer_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][ACC_TIMESTAMP_POSITION])
        accelerometer_timestamp_dict['X'].append(accelerometer_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][ACC_X_POSITION])
        accelerometer_timestamp_dict['Y'].append(accelerometer_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][ACC_Y_POSITION])
        accelerometer_timestamp_dict['Z'].append(accelerometer_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][ACC_Z_POSITION])
    acc_per_shot_arr.append(accelerometer_timestamp_dict)
    
    # GYRO
    for dataPointIdx in range(len(gyroscope_master_list[shotIdx])):
        gyroscope_timestamp_dict['timestamp'].append(gyroscope_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][GYRO_TIMESTAMP_POSITION])
        gyroscope_timestamp_dict['X'].append(gyroscope_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][GYRO_X_POSITION])
        gyroscope_timestamp_dict['Y'].append(gyroscope_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][GYRO_Y_POSITION])
        gyroscope_timestamp_dict['Z'].append(gyroscope_master_list[shotIdx][dataPointIdx][TUPLE_DATA_POSITION][GYRO_Z_POSITION])
    gyro_per_shot_arr.append(gyroscope_timestamp_dict)
    
LIGHT_THRESHOLD = 300

# Calculate the index to truncate after in a timestamp sorted dataframe
def calculate_truncate_index(sorted_sample_light_df, shot_number):
  num_indexes = sorted_sample_light_df.shape[0]
  for i in range(int(num_indexes)):
    if sorted_sample_light_df.at[i, 'light'] > LIGHT_THRESHOLD:
      return i

  raise Exception(f"Light readings for shot number {shot_number} never exceeded threshold!")


def pad_data(df, list):
  padded_df = df
  while padded_df.shape[0] < 50:
    padded_df = padded_df.append(list, ignore_index=True)
  return padded_df


#Merged data of shotNumber  in to 1 sample dataframe
def get_sample_df(shotNumber):
    sample_light_df = pd.DataFrame(light_per_shot_arr[shotNumber]).sort_values(["timestamp"],kind='mergesort', ignore_index=True).drop(columns=["timestamp"]).rename(columns={"reading" : "light"})
    truncate_index = calculate_truncate_index(sample_light_df, shotNumber)
    sample_light_df = sample_light_df.truncate(after=truncate_index)
    sample_light_df = pad_data(sample_light_df,{'light': 0})
    
    sample_acc_df = pd.DataFrame(acc_per_shot_arr[shotNumber]).sort_values(["timestamp"],kind='mergesort',ignore_index=True).truncate(after=truncate_index).drop(columns=["timestamp"]).rename(columns={"X": "accel_X", "Y": "accel_Y", "Z": "accel_Z"})
    sample_acc_df = pad_data(sample_acc_df,{'accel_X': 0, 'accel_Y':0, 'accel_Z': 0})

    sample_gyro_df = pd.DataFrame(gyro_per_shot_arr[shotNumber]).sort_values(["timestamp"],kind='mergesort', ignore_index=True).truncate(after=truncate_index).drop(columns=["timestamp"]).rename(columns={"X": "gyro_X", "Y": "gyro_Y", "Z": "gyro_Z"})
    sample_gyro_df = pad_data(sample_gyro_df,{'gyro_X': 0, 'gyro_Y':0, 'gyro_Z': 0})

    # sample_df = pd.merge(pd.merge(sample_light_df, sample_acc_df, left_index=True, right_index=True),sample_gyro_df,left_index=True, right_index=True)
    sample_df = pd.merge(sample_acc_df, sample_gyro_df,left_index=True, right_index=True) # Without light readings
    return sample_df, truncate_index
    
def calculate_abs_accel_at_index(sample_df, index):
  return abs(sample_df.at[index, 'accel_X']) + abs(sample_df.at[index, 'accel_Y'])+ abs(sample_df.at[index, 'accel_Z'])

#store df of each shot into dict
truncate_index_accumulator = 0
abs_accel_accumulator = 0
abnormal_readings = []
sample_df_dict = {}
for shot_count in range(totalNumberOfShots):
    sample_df, truncate_index = get_sample_df(shot_count)
    truncate_index_accumulator += truncate_index
    abs_accel_at_cutoff = calculate_abs_accel_at_index(sample_df, truncate_index)
    abs_accel_accumulator += abs_accel_at_cutoff
    # print(f"Throw Number: {shot_count+1} , Truncate Index: {truncate_index}") # For debugging...
    if  abs_accel_at_cutoff < 1:
      abnormal_readings.append({'throw_num': shot_count+1, 'truncate_index': truncate_index, 'abs_accel': abs_accel_at_cutoff})
    sample_df_dict[shot_count] = sample_df

print("Average truncate index: ", truncate_index_accumulator/(totalNumberOfShots))
print("Average accel at truncate index: ", abs_accel_accumulator/(totalNumberOfShots))




#convert and append df of shots to numpy array 
samples_input_array = np.array([])
sample_array_to_append = np.array([])
for i in range(1):
    sample_array_to_append = sample_df_dict[i].to_numpy()
    samples_input_array = np.append(samples_input_array, sample_array_to_append)
    

#reshape samples array
#TODO normalize/scale data
samples_size = 1     #number of shots
timestamp_size = 50   #based on truncate value 
features = 6         #7 features(light, accelXYZ, gyroXYZ) should be 6 features when we truncate with light sensor

X = samples_input_array.reshape(samples_size,timestamp_size,features)
X.shape
print(X[0])

#======================== collab ends here =======================
print(X[0].shape)
temp2 = X[0].reshape(1,50,6)
Temp = np.argmax(model.predict(temp2), axis=-1)
print(Temp)
if Temp == 0:
  print("You missed, try harder next time")
else:
  print("You scored!")