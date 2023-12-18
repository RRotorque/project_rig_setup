import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("topic/stream", qos=1)

def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode('utf-8')}")
    # Process the message here

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.loop_forever()
