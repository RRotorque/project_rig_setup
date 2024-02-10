import tkinter as tk
from tkinter import scrolledtext, ttk, Button,messagebox,filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2Tk
from matplotlib.figure import Figure
from PIL import Image, ImageTk
import numpy as np
import serial
import serial.tools.list_ports
import threading
import json
import pandas as pd
import socket
import paho.mqtt.client as mqtt
from matplotlib.animation import FuncAnimation
import datetime

# Declare com_combobox as a global variable
com_combobox = None
is_connected = False
serial_port = None
serial_thread = None
data_text = None  # Corrected to avoid conflicts

# Sample data for each graph
x_data1 = []
y_data1 = []

x_data2 = []
y_data2 = []

x_data3 = []
y_data3 = []

def get_available_com_ports():
    com_ports = [port.device for port in serial.tools.list_ports.comports()]
    return com_ports


def read_sensor_value():
    global is_connected, serial_port, scrolled_text2
    while is_connected:
        try:
            if serial_port.is_open:
                data = serial_port.readline().decode('utf-8', errors='replace').strip()
                print("Received data:", data)  # For debugging

                # Directly update the scrolled_text2 widget
                scrolled_text2.config(state=tk.NORMAL)
                scrolled_text2.insert(tk.END, data + '\n')
                scrolled_text2.config(state=tk.DISABLED)
                scrolled_text2.see(tk.END)  # Scroll to the end
        except serial.SerialException:
            disconnect()
            # Directly update the scrolled_text2 widget
            scrolled_text2.config(state=tk.NORMAL)
            scrolled_text2.insert(tk.END, "Connection closed.\n")
            scrolled_text2.config(state=tk.DISABLED)
            scrolled_text2.see(tk.END)  # Scroll to the end
            break

def connect():
    global is_connected, serial_port, serial_thread, com_port_var, baud_rate_var, message_text, connect_button, refresh_button, com_combobox, data_text

    if not is_connected:
        try:
            serial_port = serial.Serial(port=com_port_var.get(), baudrate=int(baud_rate_var.get()), timeout=1)
            is_connected = True

            serial_thread = threading.Thread(target=read_sensor_value)
            serial_thread.start()

            scrolled_text2.insert(tk.END, "Connected to {} with baud rate {}\n".format(com_port_var.get(), baud_rate_var.get()))

            # Update button and combobox states
            connect_button.configure(text="Disconnect")
            refresh_button.configure(state="disabled")
            com_combobox.configure(state="disabled")
        except serial.SerialException as e:
            messagebox.showerror("Error", str(e))
    else:
        disconnect()



def disconnect():
    global is_connected, serial_port, message_text, connect_button, refresh_button, com_combobox

    if is_connected:
        is_connected = False
        serial_port.close()
        message_text.insert(tk.END, "Disconnected\n")

        # Update button and combobox state
        connect_button.configure(text="Connect")
        refresh_button.configure(state="normal")
        com_combobox.configure(state="readonly")


def refresh_ports():
    global com_combobox
    if com_combobox:
        com_ports = get_available_com_ports()
        com_combobox['values'] = com_ports

def read_data():
    while is_connected:
        try:
            data = serial_port.readline()
            decoded_data = data.decode('utf-8', errors='replace').strip()
            scrolled_text2.insert(tk.END, decoded_data + '\n')
        except serial.SerialException:
            disconnect()
            tk.messagebox.showinfo("Info", "Connection closed.")
            break








#MQTT LAYER


# def update_scrolled_text2(self, new_data):
#     """Update the content of scrolled_text2."""
#     self.scrolled_text2.config(state=tk.NORMAL)  # Set state to normal to allow editing
#     self.scrolled_text2.delete(1.0, tk.END)  # Clear existing content
#     self.scrolled_text2.insert(tk.END, new_data)  # Insert new data
#     self.scrolled_text2.config(state=tk.DISABLED)  # Set state back to disabled

def connect_to_broker():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    broker_address = broker_entry.get()
    port_number = int(port_combobox.get())
    topic = topic_entry.get()

    try:
        # Set up on_connect and on_message callbacks if needed
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(broker_address, port_number, 60)
        # Start the loop after connection
        client.loop_start()

        # Subscribe to the specified topic
        client.subscribe(topic)

        # Optionally, you can do additional setup or GUI updates here
    except socket.gaierror:
        connection_status_label.config(text="Invalid broker address", fg="red")

def on_connect(*args):
    
    if args:
        client, userdata, flags, rc = args
    global is_connected, broker_entry, port_combobox, topic_entry, refresh_button, scrolled_text2

    if rc == 0:
        print(f"Connected to {broker_entry.get()}:{port_combobox.get()}")
        connection_status_label.config(text="Connected successfully", fg="green")
        topic_to_subscribe = topic_entry.get()
        client.subscribe(topic_to_subscribe)
        print(f"Subscribed to {topic_to_subscribe} successfully")

        # Enable the refresh button after connecting
        refresh_button.config(state=tk.NORMAL)

        # Update the scrolled_text2 widget
        scrolled_text1.config(state=tk.NORMAL)
        # scrolled_text1.insert(tk.END, "Connected to broker successfully.\n")
        scrolled_text1.config(state=tk.DISABLED)
        scrolled_text1.see(tk.END)  # Scroll to the end
    else:
        print(f"Connection failed with result code {rc}")
        if rc == 5:  # Authentication error
            messagebox.showerror("Connection Error", "Authentication failed. Check username and password.")
        elif rc == 4:  # Connection refused - bad broker address
            connection_status_label.config(text="Invalid broker address", fg="red")
        else:
            connection_status_label.config(text=f"Connection failed (Code {rc})", fg="red")

        # Disable the refresh button after connecting
        refresh_button.config(state=tk.DISABLED)

def update_gui(message):
    scrolled_text1.config(state=tk.NORMAL)
    scrolled_text1.insert(tk.END, f"{message}\n")
    scrolled_text1.config(state=tk.DISABLED)
    scrolled_text1.yview(tk.END)  # Scroll to the bottom


def extract_minutes_from_time(time_str):
    time_obj = datetime.datetime.strptime(time_str, "%H:%M:%S").time()
    return time_obj.minute

def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    print(f"Received message: {message}")
    update_gui(message)

    payload = msg.payload.decode('utf-8')
    data = json.loads(payload)

    x_point = data.get('time')
    y_point_reading = data.get('reading')
    y_point_voltage = data.get('voltage')

    minutes = extract_minutes_from_time(x_point)

    #time vs thrust
    x_data1.append(minutes)
    y_data1.append(y_point_reading)

    #thruust vs voltage
    x_data2.append(y_point_reading)
    y_data2.append(y_point_voltage)

    #time vs voltage
    x_data3.append(minutes)
    y_data3.append(y_point_voltage)

    # Enable the refresh button after receiving a message
    refresh_button.config(state=tk.NORMAL)

    # Generate and update the report preview
    root.after(100, update_report_preview)

    # # Display the received data in scrolled_text2
    # scrolled_text1.config(state=tk.NORMAL)
    # scrolled_text1.insert(tk.END, f"Received message: {message}\n")
    # scrolled_text1.config(state=tk.DISABLED)
    # scrolled_text1.see(tk.END)  # Scroll to the end

def update_report_preview():
    # Check if there is any data to generate a report
    if not x_data1 or not y_data2:
        return

    # Assuming you want to use the existing data structures
    df = pd.DataFrame({
        'time': x_data1,
        'voltage': y_data2,
        'reading': y_data2
    })

    # Calculate changes in voltage and reading
    df['Voltage Change'] = df['voltage']
    df['Reading Change'] = df['reading']

    # Extracting key metrics for analysis
    max_voltage_change = df['Voltage Change'].max()
    min_voltage_change = df['Voltage Change'].min()

    max_reading_change = df['Reading Change'].max()
    min_reading_change = df['Reading Change'].min()

    # Generate a brief report
    report = f"""
    ## Voltage and Reading Change Analysis

    ### Key Metrics

    - **Maximum Voltage:** {max_voltage_change}
    - **Minimum Voltage:** {min_voltage_change}

    - **Maximum Thrust:** {max_reading_change}
    - **Minimum Thrust:** {min_reading_change}

    ### Comparison Analysis

    The analysis focuses on changes in voltage and sensor readings over time:

    ### Reading vs Time Analysis

    To find the time corresponding to specific values of the reading:
    """

    # Update the content of the scrolled_text3 widget
    scrolled_text3.config(state=tk.NORMAL)
    scrolled_text3.delete(1.0, tk.END)
    scrolled_text3.insert(tk.END, report)
    scrolled_text3.config(state=tk.DISABLED)
    scrolled_text3.yview(tk.END)  # Scroll to the bottom









def main():
    global message_text, com_port_var, baud_rate_var, com_combobox, connect_button, refresh_button, data_text, \
        root, scrolled_text2, scrolled_text1, scrolled_text3, connection_status_label, broker_entry, topic_entry, port_combobox

    root = tk.Tk()

    # Set up your logo image
    logo_image = Image.open(open("logo.png", 'rb'))
    logo_image = logo_image.resize((32, 32))
    logo_image = ImageTk.PhotoImage(logo_image)
    root.iconphoto(True, logo_image)

    root.title("Tkinter with Matplotlib Example")

    baud_rate_var = tk.StringVar()
    baud_rate_var.set("9600")

    com_ports = get_available_com_ports()
    com_port_var = tk.StringVar()
    com_port_var.set(com_ports[0] if com_ports else "")

    # Create a header frame
    header_frame = tk.Frame(root)
    header_frame.pack(fill='x')

    # Broker entry and label in the header frame
    broker_label = tk.Label(header_frame, text="Broker:")
    broker_label.grid(row=1, column=0)
    broker_entry = tk.Entry(header_frame)
    broker_entry.grid(row=1, column=1)

    # Topic entry in the header frame
    topic_label = tk.Label(header_frame, text="Topic:")
    topic_label.grid(row=1, column=2)
    topic_entry = tk.Entry(header_frame)
    topic_entry.grid(row=1, column=3)

    # Port label in the header frame
    port_label = tk.Label(header_frame, text="Port:")
    port_label.grid(row=1, column=4)

    # Port combobox in the header frame
    port_combobox = ttk.Combobox(header_frame, values=["1883", "8883"])  # Add more port values as needed
    port_combobox.set("1883")  # Set a default value
    port_combobox.grid(row=1, column=5)

    # Connect button in the header frame
    connect_button1 = ttk.Button(header_frame, text="Connect", command=connect_to_broker)
    connect_button1.grid(row=1, column=6, padx=10)

    # Connection status label in the header frame
    connection_status_label = tk.Label(header_frame, text="", fg="black")
    connection_status_label.grid(row=1, column=7, padx=10)

    # Refresh button in the header frame
    refresh_button = Button(header_frame, text="Refresh", command=clear_data)
    refresh_button.grid(row=1, column=8, padx=10, pady=10)

    # Com label in the header frame
    com_label = tk.Label(header_frame, text="Com Port:")
    com_label.grid(row=1, column=10)

    # Com combobox in the header frame
    com_combobox = ttk.Combobox(header_frame, textvariable=com_port_var, values=com_ports)
    com_combobox.grid(row=1, column=11)

    # Schedule the refresh_ports function to be called after the mainloop starts
    root.after(100, refresh_ports)

    # Baud rate label in the header frame
    baud_rate_label = tk.Label(header_frame, text="Baud Rate:")
    baud_rate_label.grid(row=1, column=12)

    # Baud rate combobox in the header frame
    baud_rate_combobox = ttk.Combobox(header_frame, textvariable=baud_rate_var, values=["9600", "115200"])
    baud_rate_combobox.grid(row=1, column=13)

    # Connect button in the header frame
    connect_button = ttk.Button(header_frame, text="Connect", command=connect)
    connect_button.grid(row=1, column=14)

    # Save button in the header frame
    save_button = ttk.Button(header_frame, text="Save", command=save_content)
    save_button.grid(row=1, column=15, padx=10)

    # Refresh button in the header frame
    refresh_button = ttk.Button(header_frame, text="Refresh", command=refresh_ports)
    refresh_button.grid(row=1, column=16, padx=10, pady=10)

    # Generate report button in the header frame
    generate_report_button = ttk.Button(header_frame, text="Generate Report", command=generate_report)
    generate_report_button.grid(row=1, column=17, padx=10, sticky="e")

    # Serial Communication
    serial_port = None
    serial_thread = None

    # ... (Rest of the header frame code remains unchanged)

    content_frame = tk.Frame(root)
    content_frame.pack(fill='both', expand=True)

    # Create header labels above each ScrolledText area
    label1 = tk.Label(content_frame, text="MQTT Connection")
    label1.grid(row=0, column=0, pady=(0, 10))

    label2 = tk.Label(content_frame, text="COM Connection")
    label2.grid(row=0, column=1, pady=(0, 10))

    label3 = tk.Label(content_frame, text="Report View")
    label3.grid(row=0, column=2, pady=(0, 10))

    # Create ScrolledText widgets inside labels
    scrolled_text1 = create_scrolled_text(content_frame)
    scrolled_text1.grid(row=1, column=0, sticky="nsew")

    scrolled_text2 = create_scrolled_text(content_frame)
    scrolled_text2.grid(row=1, column=1, sticky="nsew")

    scrolled_text3 = create_scrolled_text(content_frame)
    scrolled_text3.grid(row=1, column=2, sticky="nsew")

    # Set row weight for resizing
    content_frame.rowconfigure(1, weight=1)

    graph_frame = tk.Frame(root)
    graph_frame.pack(fill='both', expand=True)

    canvas1, toolbar1, update_func1 = create_live_matplotlib_figure_with_toolbar(graph_frame, "Graph 1", x_data1, y_data1, row=0, col=0)
    canvas2, toolbar2, update_func2 = create_live_matplotlib_figure_with_toolbar(graph_frame, "Graph 2", x_data2, y_data2, row=0, col=1)
    canvas3, toolbar3, update_func3 = create_live_matplotlib_figure_with_toolbar(graph_frame, "Graph 3", x_data3, y_data3, row=0, col=2)

    # Set equal column weights for resizing
    graph_frame.columnconfigure(0, weight=1)
    graph_frame.columnconfigure(1, weight=1)
    graph_frame.columnconfigure(2, weight=1)

    # Set row weight for resizing
    graph_frame.rowconfigure(0, weight=1)

    # Start the animation without caching frame data
    ani1 = FuncAnimation(canvas1.figure, update_func1, blit=False, cache_frame_data=False)
    ani2 = FuncAnimation(canvas2.figure, update_func2, blit=False, cache_frame_data=False)
    ani3 = FuncAnimation(canvas3.figure, update_func3, blit=False, cache_frame_data=False)


    # ... (Rest of the graph frame code remains unchanged)

    root.mainloop()


def create_live_matplotlib_figure_with_toolbar(parent, title, x_data, y_data, row, col):
    figure = Figure(figsize=(6, 4), dpi=100)
    subplot = figure.add_subplot(1, 1, 1)
    subplot.set_title(title)
    subplot.set_xlabel("X-axis", labelpad=0)
    subplot.set_ylabel("Y-axis", labelpad=0)

    # Create a Frame to hold both the canvas and the toolbar
    graph_frame = tk.Frame(parent)
    graph_frame.grid(row=row, column=col, sticky="nsew")

    # Prevent the frame from adjusting its size to fit its children
    graph_frame.pack_propagate(0)

    # Create Matplotlib toolbar
    toolbar = NavigationToolbar2Tk(figure.canvas, graph_frame)
    toolbar.update()
    toolbar.grid(row=0, column=0, sticky="nsew", padx=30, pady=10)

    # Create Matplotlib canvas
    canvas = FigureCanvasTkAgg(figure, master=graph_frame)
    canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=30, pady=10)

    # Set equal row weights for resizing in the new frame
    graph_frame.rowconfigure(0, weight=0)  # Toolbar
    graph_frame.rowconfigure(1, weight=1)  # Canvas

    # Define the update function for animation
    def update_func(frame):
        update_data(frame, subplot, x_data, y_data, title, canvas)

    return canvas, toolbar, update_func


def update_data(frame, subplots, x_data, y_data_sets, titles, canvas):
    for i, (subplot, x_data, y_data, title) in enumerate(zip(subplots, x_data, y_data_sets, titles)):
        # Update the line data
        line = subplot.lines[0]
        line.set_xdata(x_data)
        line.set_ydata(y_data)

        if title == "Graph 1":
            subplot.set_title(title)
            subplot.set_xlabel("Time", labelpad=0)
            subplot.set_ylabel("Voltage", labelpad=0)
        elif title == "Graph 2":
            subplot.set_title(title)
            subplot.set_xlabel("Voltage", labelpad=0)
            subplot.set_ylabel("Thrust", labelpad=0)
        elif title == "Graph 3":
            subplot.set_title(title)
            subplot.set_xlabel("Thrust", labelpad=0)
            subplot.set_ylabel("Time", labelpad=0)

    canvas.draw()
def generate_report():
    # Get the content from scrolled_text3
    report_content = scrolled_text3.get("1.0", tk.END).strip()

    # Check if there is data before generating the report
    if report_content:
        # Use asksaveasfilename to prompt the user for file location and name
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            # Implement your saving logic here
            # Example: Save the content to the specified file
            with open(file_path, "w") as file:
                file.write(report_content)

            messagebox.showinfo("Save Successful", f"Report saved to {file_path} successfully.")
        else:
            messagebox.showwarning("No File Selected", "Please select a file location.")
    else:
        messagebox.showwarning("No Data", "No data available to generate a report.")

def save_content():
    # Get the content from COM and MQTT connections
    com_content = scrolled_text2.get("1.0", tk.END).strip()
    mqtt_content = scrolled_text1.get("1.0", tk.END).strip()

    # Check if there is data before saving
    if com_content or mqtt_content:
        # Use asksaveasfilename to prompt the user for file location and name
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )

        if file_path:
            # Implement your saving logic here
            # Example: Save the content to the specified file
            with open(file_path, "w") as file:
                if com_content:
                    file.write("COM Connection:\n" + com_content + "\n\n")
                if mqtt_content:
                    file.write("MQTT Connection:\n" + mqtt_content + "\n\n")

            messagebox.showinfo("Save Successful", f"Content saved to {file_path} successfully.")
        else:
            messagebox.showwarning("No File Selected", "Please select a file location.")
    else:
        messagebox.showwarning("No Data", "No data to save.")

def create_scrolled_text(parent):
    scrolled_text = scrolledtext.ScrolledText(parent, state=tk.DISABLED)
    return scrolled_text

def create_matplotlib_figure(title, x_data, y_data):
    figure = Figure(figsize=(5, 4), dpi=100)
    subplot = figure.add_subplot(1, 1, 1)
    subplot.plot(x_data, y_data)
    subplot.set_title(title)
    subplot.set_xlabel("X-axis")
    subplot.set_ylabel("Y-axis")

    return figure

def clear_data():
    # Implement functionality to clear data or refresh as needed
    pass

# def connect_to_broker():
#     broker_address = broker_entry.get()
#     port_number = int(port_combobox.get())
#     topic = topic_entry.get()

#     try:
#         client.connect(broker_address, port_number, 60)
#         client.loop_start()  # Start the loop after connection
#         client.subscribe(topic)
#     except socket.gaierror:
#         connection_status_label.config(text="Invalid broker address", fg="red")


if __name__ == "__main__":
    main()