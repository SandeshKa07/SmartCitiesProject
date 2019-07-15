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
import ast
import socket

# Import MQTT client modules
import paho.mqtt.client as mqtt

sys.path.append('/home/pi/GrovePi/Software/Python/grove_rgb_lcd')
from grovepi import *
from grove_rgb_lcd import *

# Import Plugwise modules for both stick and circle
from plugwise import Stick
from plugwise import Circle

# MAC ID for both the Circles
mac1 = "000D6F0003BD7F1F"
mac2 = "000D6F0002C0DE2E"

# Plugwise Stick port
plugwise_stick = Stick(port="/dev/ttyUSB0")

# Binding each circle to the stick
plugwise_Circle_1 = Circle(mac1, plugwise_stick) # for heater
plugwise_Circle_2 = Circle(mac2, plugwise_stick) # lamp

# turning off the devices conected to circles by default
plugwise_Circle_1.switch_off()
plugwise_Circle_2.switch_off()


# Sensor Pin configuration
# Analog Port Declaration for the Sensors
sound_sensor_port = 0 # sound sensor in analog port 0

# Digital Port Declaration
ultra_sound_sensor_port = 2

# Setting the PinModes
grovepi.pinMode(sound_sensor_port,"INPUT")

# Threshold for light sensor
sound_threshold_level = 70
ultra_sound_threshold_level = 20

light_status = False
heater_status = False

indicator_led_1 = 4
indicator_led_2 = 3
''' Data Packet containing all the sensor information to be transmitted to
    MQTT Server via client running on raspberry PI.
'''

# Define event callbacks

def on_connect(mosq, obj, rc):
    print("" )

def on_message(mosq, obj, msg):
    global light_status
    global heater_status
    message_from_broker = str(msg.payload.decode("utf-8"))

    if "/heater" in msg.topic:
        heater_status = ast.literal_eval(message_from_broker)

    if "/light" in msg.topic:
        light_status = ast.literal_eval(message_from_broker)

def on_publish(mosq, obj, mid):
    #print("mid: " + str(mid))
    print ("")

def on_subscribe(mosq, obj, mid, granted_qos):
    print("This means broker has acknowledged my subscribe request")
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(mosq, obj, level, string):
    print(string)

client = mqtt.Client()

# Assign event callbacks
client.on_message = on_message
client.on_connect = on_connect
client.on_publish = on_publish
client.on_subscribe = on_subscribe

# Uncomment to enable debug messages
#client.on_log = on_log

# user name has to be called before connect - my notes.
client.username_pw_set("ndcvwock", "yotAE_3zRCsF")

client.connect('m24.cloudmqtt.com', 10480, 60)

client.loop_start()
client.subscribe ("/light",0)
client.subscribe ("/heater",0)

userpresent = "user"
nouserpresent = "nouser"

def sense_and_actuate():
    # Continuous Sensing of ultrasound and sound sensors.
    ## Sensing ultrasound and sound sensors.
    sensed_ultra_sound_value = 0
    sensed_sound_value = 0
    global light_status
    global heater_status
    socket_office_obj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    socket_office_obj.bind(('localhost', 6970))
    while True:
        try:
            for x in range(0, 9):
                sensed_ultra_sound_value += ultrasonicRead(ultra_sound_sensor_port)
                sensed_sound_value += grovepi.analogRead(sound_sensor_port)
                time.sleep(0.5)

            ultra_sound_value = sensed_ultra_sound_value/10
            sound_value =  sensed_sound_value/10
            sensed_ultra_sound_value = 0
            sensed_sound_value = 0

            if((ultra_sound_value < ultra_sound_threshold_level) or (sound_value > sound_threshold_level)):
                print("User Present at his desk, monitor power socket is turned on\n")
                socket_office_obj.sendto(nouserpresent.encode('utf-8'), ("127.0.0.1", 6969))
                time.sleep(2)
                data_received, from_address = socket_office_obj.recvfrom(1024)
                data_received = json.loads(data_received.decode())
                action_1 = data_received['action_1']
                action_2 = data_received['action_2']
                print("Action 1 : ", action_1)
                print("Action 2 : ", action_2)
                plugwise_Circle_1.switch_on()
                plugwise_Circle_2.switch_on()
            else:
                print("User not present, Saving power by turning monitor off\n")
                socket_office_obj.sendto(userpresent.encode('utf-8'), ("127.0.0.1", 6969))
                print("data sent to planner, now waiting")
                data_received, from_address = socket_office_obj.recvfrom(1024)
                data_received = json.loads(data_received.decode())
                action_1 = data_received['action_1']
                action_2 = data_received['action_2']
                print("Action 1 : ", action_1)
                print("Action 2 : ", action_2)
                plugwise_Circle_1.switch_off()
                plugwise_Circle_2.switch_off()

            setRGB(0,128,64)
            setRGB(0,255,0)
            setText("Light : " + str(light_status) + "   Heater: " + str(heater_status))

        except KeyboardInterrupt:
            print("Keyboard Interrupted\n")
            sys.exit(1)
        except TypeError as te:
            print("Type Error occurred\n")
            print(te)
        except IOError:
            print("Input output Error occurred\n")

def main():
    sense_and_actuate()

if __name__ == '__main__':
    main()
