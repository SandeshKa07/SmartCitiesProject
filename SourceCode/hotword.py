#!/usr/bin/env python


from __future__ import print_function
import argparse
import json
import os.path
import pathlib2 as pathlib
import grovepi
import google.oauth2.credentials
import sys
import os
import time
import threading

# Google assistant imports.
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device

#Fault handler for google assistant
import faulthandler

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

# Binding each circle to the stick
plugwise_Circle_1 = Circle(mac1, plugwise_stick) # for heater
plugwise_Circle_2 = Circle(mac2, plugwise_stick) # lamp

# turning off the devices conected to circles by default
plugwise_Circle_1.switch_off()
plugwise_Circle_2.switch_off()

# Configure thingsboard host and Access_token
THINGSBOARD_HOST = '141.58.216.26'
ACCESS_TOKEN = 'DHT-48Data'

# Home Sensor Data captured and uploaded interval in seconds.
INTERVAL=10

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


# Sensor Pin configuration
# Analog Port Declaration for the Sensors
light_sensor_port = 0   # Grove Light Sensor on A0 Port

# Digital Port Declaration
digital_humidity_temperature_sensor_port = 2
ultra_sound_sensor_port = 3
indicator_led = 4

# Setting the PinModes
grovepi.pinMode(light_sensor_port, "INPUT")
grovepi.pinMode(indicator_led, "OUTPUT")
grovepi.digitalWrite(indicator_led, 0)


# Placeholders for all the sensors.
temperature_humidity_sensor_data = {'temperature': 0, 'humidity': 0, '':0,}

# Threshold for light sensor
threshold_light_sensor = 10



''' Data Packet containing all the sensor information to be transmitted to 
    MQTT Server via client running on raspberry PI.'''

# Enable the fault handler.
faulthandler.enable()

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


WARNING_NOT_REGISTERED = """
    This device is not registered. This means you will not be able to use
    Device Actions or see your device in Assistant Settings. In order to
    register this device follow instructions at:

    https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device
"""


def process_event(event):
    """Pretty prints events.

    Prints all events that occur with two spaces between each new
    conversation and a single space between turns of a conversation.

    Args:
        event(event.Event): The current event to process.
    """
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        print()

    print(event)

    print("event type = ", event.type)
    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and not event.args['with_follow_on_turn']):
        print()
    if event.type == EventType.ON_DEVICE_ACTION:
        for command, params in event.actions:
            print('Do command', command, 'with params', str(params))
            if command == "action.devices.commands.OnOff":
                if params['on']:
                    print('Turning LIGHT on.')
                    plugwise_Circle_2.switch_on()
                    grovepi.digitalWrite(indicator_led,1) # temporary as of now, delete when we have plugwise

                else:
                    print('Turning LIGHT off.')
                    plugwise_Circle_2.switch_off()
                    grovepi.digitalWrite(indicator_led,0) # temporary as of now, delete when we have plugwise

            if command == "action.devices.commands.StartStop":
                if params['start']:
                    print('Turning HEATER on.')
                    plugwise_Circle_1.switch_on()
                    grovepi.digitalWrite(indicator_led, 1)  # temporary as of now, delete when we have plugwise

                else:
                    print('Turning HEATER off.')
                    plugwise_Circle_1.switch_off()
                    grovepi.digitalWrite(indicator_led, 0)  # temporary as of now, delete when we have plugwis


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--device-model-id', '--device_model_id', type=str,
                        metavar='DEVICE_MODEL_ID', required=False,
                        help='the device model ID registered with Google')
    parser.add_argument('--project-id', '--project_id', type=str,
                        metavar='PROJECT_ID', required=False,
                        help='the project ID used to register this device')
    parser.add_argument('--nickname', type=str,
                        metavar='NICKNAME', required=False,
                        help='the nickname used to register this device')
    parser.add_argument('--device-config', type=str,
                        metavar='DEVICE_CONFIG_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'googlesamples-assistant',
                            'device_config_library.json'
                        ),
                        help='path to store and read device configuration')
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='path to store and read OAuth2 credentials')
    parser.add_argument('--query', type=str,
                        metavar='QUERY',
                        help='query to send as soon as the Assistant starts')
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + Assistant.__version_str__())

    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))

    device_model_id = None
    last_device_id = None
    try:
        with open(args.device_config) as f:
            device_config = json.load(f)
            device_model_id = device_config['model_id']
            last_device_id = device_config.get('last_device_id', None)
    except FileNotFoundError:
        pass

    if not args.device_model_id and not device_model_id:
        raise Exception('Missing --device-model-id option')

    # Re-register if "device_model_id" is given by the user and it differs
    # from what we previously registered with.
    should_register = (
        args.device_model_id and args.device_model_id != device_model_id)

    device_model_id = args.device_model_id or device_model_id

    with Assistant(credentials, device_model_id) as assistant:
        events = assistant.start()

        device_id = assistant.device_id
        print('device_model_id:', device_model_id)
        print('device_id:', device_id + '\n')


        # Re-register if "device_id" is different from the last "device_id":
        if should_register or (device_id != last_device_id):
            if args.project_id:
                register_device(args.project_id, credentials,
                                device_model_id, device_id, args.nickname)
                pathlib.Path(os.path.dirname(args.device_config)).mkdir(
                    exist_ok=True)
                with open(args.device_config, 'w') as f:
                    json.dump({
                        'last_device_id': device_id,
                        'model_id': device_model_id,
                    }, f)
            else:
                print(WARNING_NOT_REGISTERED)

        for event in events:
            if event.type == EventType.ON_START_FINISHED and args.query:
                assistant.send_text_query(args.query)

            process_event(event)

        try:
            while True:
                # Continuous Sensing of Temperature and light sensors.

                ## Sensing Temperature and humidity
                [temperature, humidity] = grovepi.dht(digital_humidity_temperature_sensor_port, 0)
                print("Temperature = %.02f C, Humidity = %.02f %%" % (temperature, humidity))
                temperature_humidity_sensor_data['temperature'] = temperature
                temperature_humidity_sensor_data['humidity'] = humidity

                # Sensing light threshold.
                light_sensor_value = grovepi.analogRead(light_sensor_port)
                resistance = (float)(1023 - light_sensor_value) * 10 / light_sensor_value

                # Decision making and actuating.
                if(temperature < 15):
                    plugwise_Circle_1.switch_on()
                else:
                    plugwise_Circle_1.switch_off()

                if(resistance > threshold_light_sensor):
                    plugwise_Circle_2.switch_on()
                    grovepi.digitalWrite(indicator_led, 1) # temporary as of now, delete when we have plugwise.
                else:
                    plugwise_Circle_2.switch_off()
                    grovepi.digitalWrite(indicator_led, 0) # temporary as of now, delete when we have plugwise.


                #client.publish('v1/devices/me/telemetry', json.dumps(temperature_humidity_sensor_data), 1)

                #next_reading += INTERVAL
                #sleep_time = next_reading - time.time()
                #if sleep_time > 0:
                 #   time.sleep(sleep_time)

        except KeyboardInterrupt:
            pass




if __name__ == '__main__':
    main()
