import grovepi
from plugwise import Stick
from plugwise import Circle
import sys
import os
import time
import sys
import paho.mqtt.client as mqtt
import json

port=7
sensor=0
mac1 = "000D6F0004B1E1D6"
mac2 = "000D6F0003562BE1"

THINGSBOARD_HOST = '141.58.216.26'
ACCESS_TOKEN = 'DHT-48Data'

# Data capture and upload interval in seconds. Less interval will eventually hang the DHT22.
INTERVAL=2

sensor_data = {'temperature': 0, 'humidity': 0}

next_reading = time.time() 

client = mqtt.Client()

# Set access token
client.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
client.connect(THINGSBOARD_HOST, 1883, 60)

client.loop_start()

#s = Stick(port="/dev/ttyUSB0")
#c1 = Circle(mac1, s)
#c2 = Circle(mac2, s)


#[temperature,humidity] = grovepi.dht(port,sensor)
#print("Temperature = %.02f C, Humidity = %.02f %%"%(temperature,humidity))

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

client.loop_stop()
client.disconnect()

