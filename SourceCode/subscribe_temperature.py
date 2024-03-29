import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, rc, *extra_params):
   print('Connected with result code '+str(rc))
   #print('***' + str(r))
   # Subscribing in on_connect() means that if we lose the connection and
   # reconnect then subscriptions will be renewed.
   client.subscribe('v1/devices/me/attributes')


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
   print 'Topic: ' + msg.topic + '\nMessage: ' + str(msg.payload)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
#client.publish('v1/devices/me/attributes/request/1', "{\"clientKeys\":\"model\"}", 1)

client.username_pw_set("DHT-48Data")
client.connect('141.58.57.176', 1883, 1)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
