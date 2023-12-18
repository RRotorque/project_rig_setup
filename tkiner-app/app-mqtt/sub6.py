import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import json
import tkinter as tk

# Variables for storing x, y data
x_data = []
y_data = []

# Callback when a message is received
def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    data = json.loads(payload)
    
    x_point = data.get('x')
    y_point = data.get('y')

    x_data.append(x_point)
    y_data.append(y_point)


def update_plot(frame):
    if x_data:
        line.set_data(x_data, y_data)
        ax.relim()
        ax.autoscale_view()

# MQTT setup
client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.subscribe("topic/stream")
client.loop_start()

# Tkinter setup
root = tk.Tk()
root.title("Real-Time Graph")

# Create a Matplotlib figure
fig, ax = plt.subplots()
line, = ax.plot([], [], label='Live Plot')
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.legend()

# Embed Matplotlib plot in Tkinter window
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# Use Matplotlib animation to update the plot
ani = FuncAnimation(fig, update_plot, interval=1000)  # 1000 milliseconds (1 second) update interval

# Keep the Tkinter window running
try:
    root.mainloop()
except KeyboardInterrupt:
    print("Received keyboard interrupt. Stopping the subscriber.")
    client.loop_stop()
    client.disconnect()
