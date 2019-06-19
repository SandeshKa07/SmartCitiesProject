#!/usr/bin/env python3

from __future__ import print_function
import argparse
import json
import os.path
import pathlib2 as pathlib
import grovepi
import sys
import os
import time
import threading
import concurrent.futures

# Import MQTT client modules
#import paho.mqtt.client as mqtt

# Import Plugwise modules for both stick and circle
from plugwise import Stick
from plugwise import Circle

# MAC ID for both the Circles
mac1 = "000D6F0004B1E1D6"
mac2 = "000D6F0003562BE1"

# Plugwise Stick port
#plugwise_stick = Stick(port="/dev/ttyUSB0")

# Binding each circle to the stick
#plugwise_Circle_1 = Circle(mac1, plugwise_stick) # for heater
#plugwise_Circle_2 = Circle(mac2, plugwise_stick) # lamp

# turning off the devices conected to circles by default
#plugwise_Circle_1.switch_off()
#plugwise_Circle_2.switch_off()

# Configure thingsboard host and Access_token
#THINGSBOARD_HOST = '141.58.216.26'
#ACCESS_TOKEN = 'DHT-48Data'

# Home Sensor Data captured and uploaded interval in seconds.
#INTERVAL=10

# Setting the Time Stamp for initial reading, later values are appended by INTERVAL
#next_reading = time.time()

# Initialize the MQTT client
#client = mqtt.Client()

# Set access token to which client connects
#client.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
#client.connect(THINGSBOARD_HOST, 1883, 60)

# Start the communication loop
#client.loop_start()


# Sensor Pin configuration
# Analog Port Declaration for the Sensors
light_sensor_port = 0   # Grove Light Sensor on A0 Port

# Digital Port Declaration
digital_humidity_temperature_sensor_port = 7
ultra_sound_sensor_port = 3
indicator_led_1 = 4
indicator_led_2 = 3

# Setting the PinModes
grovepi.pinMode(light_sensor_port,"INPUT")
grovepi.pinMode(indicator_led_1,"OUTPUT")
grovepi.digitalWrite(indicator_led_1, 0)
grovepi.pinMode(indicator_led_2,"OUTPUT")
grovepi.digitalWrite(indicator_led_2, 0)


# Placeholders for all the sensors.
temperature_humidity_sensor_data = {'temperature': 0, 'humidity': 0, '':0,}

# Threshold for light sensor
threshold_light_sensor = 10



''' Data Packet containing all the sensor information to be transmitted to 
    MQTT Server via client running on raspberry PI.
'''


def sense_and_actuate():
    # Continuous Sensing of Temperature and light sensors.
    # global override_assitant
    ## Sensing Temperature and humidity
    [temperature, humidity] = grovepi.dht(digital_humidity_temperature_sensor_port, 0)
    print("Temperature = %.02f C, Humidity = %.02f %%" % (temperature, humidity))
    temperature_humidity_sensor_data['temperature'] = temperature
    temperature_humidity_sensor_data['humidity'] = humidity

    time.sleep(1)
    # Sensing light threshold.
    grovepi.pinMode(light_sensor_port, "INPUT")
    light_sensor_value = grovepi.analogRead(0)
    print("light sensor value = " + str(light_sensor_value))
    resistance = (float)(1023 - light_sensor_value) * 10 / light_sensor_value
    print("Resistance = " + str(resistance))

    # Decision making and actuating.
    if (temperature < 15):
        print("cold inside, so turning heater on")
        grovepi.digitalWrite(indicator_led_2, 1)
        # plugwise_Circle_1.switch_on()
    else:
        print("Hot inside, so turning heater off")
        grovepi.digitalWrite(indicator_led_2, 0)
        # plugwise_Circle_1.switch_off()

    if (resistance > threshold_light_sensor):
        # plugwise_Circle_2.switch_on()
        print("Dark light, so turned on Lamp")
        grovepi.digitalWrite(indicator_led_1, 1)  # temporary as of now, delete when we have plugwise.
    else:
        # plugwise_Circle_2.switch_off()
        print("Bright light, so turned off Lamp")
        grovepi.digitalWrite(indicator_led_1, 0)  # temporary as of now, delete when we have plugwise.

    # client.publish('v1/devices/me/telemetry', json.dumps(temperature_humidity_sensor_data), 1)

    # next_reading += INTERVAL
    # sleep_time = next_reading - time.time()
    # if sleep_time > 0:
    #   time.sleep(sleep_time)
    print("This sensor and actuator thread is working")

def main():
    while True:
        sense_and_actuate()
        time.sleep(5)

if __name__ == '__main__':
    main()
