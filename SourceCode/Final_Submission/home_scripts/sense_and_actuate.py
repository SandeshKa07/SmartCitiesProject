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
import socket
import http.client

# Import MQTT client modules
import paho.mqtt.client as mqtt

# Import Plugwise modules for both stick and circle
from plugwise import Stick
from plugwise import Circle

# MAC ID for both the Circles
mac1 = "000D6F0004B1E1D6"
mac2 = "000D6F0000729939"

# Plugwise Stick port
plugwise_stick = Stick(port="/dev/ttyUSB0")

# Binding each circle to the stick
plugwise_Circle_1 = Circle(mac1, plugwise_stick) # for heater
plugwise_Circle_2 = Circle(mac2, plugwise_stick) # lamp

# turning off the devices conected to circles by default
plugwise_Circle_1.switch_off()
plugwise_Circle_2.switch_off()

# Configure thingsboard host and Access_token
THINGSBOARD_HOST = 'demo.thingsboard.io'
ACCESS_TOKEN = '7nl6gfO8DXf2j8Jvpkd7'

# Home Sensor Data captured and uploaded interval in seconds.
INTERVAL=10

# Setting the Time Stamp for initial reading, later values are appended by INTERVAL
next_reading = time.time()

# Initialize the MQTT client
thingsboardclient = mqtt.Client()

# Set access token to which client connects
thingsboardclient.username_pw_set(ACCESS_TOKEN)

# Connect to ThingsBoard using default MQTT port and 60 seconds keepalive interval
thingsboardclient.connect(THINGSBOARD_HOST, 1883, 60)

# Start the communication loop
thingsboardclient.loop_start()


################################################################################
# Cloud MQTT Client Publish

def on_connect(mosq, obj, rc):
    print ("on_connect:: Connected with result code "+ str ( rc ) )
    print("rc: " + str(rc))
    print("" )

def on_publish(mosq, obj, mid):
    print("Published Status to MQTT Cloud : " + str(mid))

cloudmqttclient = mqtt.Client()

# Assign event callbacks
cloudmqttclient.on_connect = on_connect
cloudmqttclient.on_publish = on_publish

cloudmqttclient.username_pw_set("ndcvwock", "yotAE_3zRCsF")
cloudmqttclient.connect('m24.cloudmqtt.com', 10480, 60)

cloudmqttclient.loop_start()
################################################################################

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

# Dashboard data
dashboard_data = {'temperature': 0, 'humidity': 0, 'light':0, 'heater_status':False, 'light_status':False, 'glight_status':False, 'gheater_status':False }

# Threshold for light sensor
threshold_light_sensor = 50
server_address = ("127.0.0.1", 6969)
initial_connection_message = "Hello Google !"


light_status = False
heater_status = False
slight_status = False
sheater_status = False

''' Data Packet containing all the sensor information to be transmitted to 
    MQTT Server via client running on raspberry PI.
'''
def listen_assistant(socket_client_obj):
    print("                                 ")
    print("thread started......")
    print("                                 ")
    while True:
        try:
            global light_status
            global heater_status
            data_received, from_address = socket_client_obj.recvfrom(1024)
            data_received = json.loads(data_received.decode())
            light_status = data_received['light']
            heater_status = data_received['heater']
            print("                                         ")
            print("light = " , str(light_status))
            print("heater = ", str(heater_status))
            print("                                         ")
        except KeyboardInterrupt:
            print("Keyboard Interrupted\n")
            sys.exit(1)


def sense_and_actuate(socket_client_obj):
    # Continuous Sensing of Temperature and light sensors.
    # global override_assitant
    ## Sensing Temperature and humidity
    resistance = 10
    while True:
        try:
            global heater_status
            global light_status
            global sheater_status
            global slight_status

            # Sensing light threshold.
            grovepi.pinMode(light_sensor_port, "INPUT")
            light_sensor_value = grovepi.analogRead(0)
            print("light sensor value = " + str(light_sensor_value))
            if(light_sensor_value > 0):
                resistance = (float)(1023 - light_sensor_value) * 10 / light_sensor_value
                print("Resistance = " + str(resistance))

            [temperature, humidity] = grovepi.dht(digital_humidity_temperature_sensor_port, 0)
            print("Temperature = %.02f C, Humidity = %.02f %%" % (temperature, humidity))
            temperature_humidity_sensor_data['temperature'] = temperature
            temperature_humidity_sensor_data['humidity'] = humidity
            
            # Decision making and actuating.
            if (temperature < 15 or heater_status == True or sheater_status == True):
                print("cold inside, so turning heater on")
                plugwise_Circle_1.switch_on()
                sheater_status = True

            elif(temperature > 15 or heater_status == False or sheater_status == False):
                print("Hot inside, so turning heater off")
                plugwise_Circle_1.switch_off()
                sheater_status = False

            if (resistance > threshold_light_sensor or light_status == True or slight_status == True):
                plugwise_Circle_2.switch_on()
                print("Dark light, so turned on Lamp")
                slight_status = True

            elif (resistance < threshold_light_sensor or light_status == False or slight_status == False):
                plugwise_Circle_2.switch_off()
                print("Bright light, so turned off Lamp")
                sligth_status = False

            if(temperature >= 15):
                sheater_status = False
            if(resistance < threshold_light_sensor):
                slight_status = False

            time.sleep(5)
            cloudmqttclient.publish( "/light", slight_status)
            cloudmqttclient.publish( "/heater", sheater_status)
            cloudmqttclient.publish( "/temperature", temperature)
            cloudmqttclient.publish( "/humidity", humidity)
            dashboard_data['temperature'] = temperature
            dashboard_data['humidity'] = humidity
            dashboard_data['light'] = light_sensor_value
            dashboard_data['heater_status'] = sheater_status
            dashboard_data['light_status'] = slight_status
            dashboard_data['gheater_status'] = heater_status
            dashboard_data['glight_status'] = light_status
            thingsboardclient.publish('v1/devices/me/telemetry', json.dumps(dashboard_data), 1)

        except KeyboardInterrupt:
            print("Keyboard Interrupted\n")
            socket_client_obj.close()
            sys.exit(1)

def main():
        socket_client_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        socket_client_obj.sendto(initial_connection_message.encode('utf-8'), ("127.0.0.1", 6969))
        #sense_and_actuate(socket_client_obj)
        listening_thread = threading.Thread(target=listen_assistant, args=(socket_client_obj,))
        listening_thread.start()
        sense_and_actuate(socket_client_obj)


if __name__ == '__main__':
    main()
