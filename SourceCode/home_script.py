# Standard Python Imports

import grovepi
import sys
import os
import time
import sys
import json

# Import MQTT client modules
import paho.mqtt.client as mqtt

# Import Plugwise modules for both stick and circle
from plugwise import Stick
from plugwise import Circle

# MAC ID for both the Circles  
mac1 = "000D6F0004B1E1D6"
mac2 = "000D6F0003562BE1"

# Plugwise Stick port
plugwise_stick = Stick(port="/dev/ttyUSB0")

# Configure thingsboard host and Access_token
THINGSBOARD_HOST = '141.58.216.26'
ACCESS_TOKEN = 'DHT-48Data'

# Home Sensor Data captured and uploaded interval in seconds.
INTERVAL=5

# Setting the Time Stamp for initial reading, later values are appended by INTERVAL
next_reading = time.time() 

# Initialize the MQTT client
client = mqtt.Client()

# Set access token to which client connects
client.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
client.connect(THINGSBOARD_HOST, 1883, 60)

# Start the communication loop
client.loop_start()

# Analog Port Declaration for the Sensors
light_sensor_port = 0   # Grove Light Sensor on A0 Port

# Digital Port Declaration
digital_humidity_temperature_sensor = 2
ultra_sound_sensor = 3
indicator_led = 4

''' Data Packet containing all the sensor information to be transmitted to 
    MQTT Server via client running on raspberry PI.'''

sensor_data = {'temperature': 0, 'humidity': 0, '':0,}

try: 
    while True:
        [temperature,humidity] = grovepi.dht(port,sensor)
        print("Temperature = %.02f C, Humidity = %.02f %%"%(temperature,humidity))
        sensor_data['temperature'] = temperature
        sensor_data['humidity'] = humidity

        client.publish('v1/devices/me/telemetry', json.dumps(sensor_data),1)

        next_reading += INTERVAL
        sleep_time = next_reading - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    pass

# Close the Communication loop of MQTT and disconnect the connection
client.loop_stop()
client.disconnect()

