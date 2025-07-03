# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-asynchronous-web-server-micropython/

# Import necessary modules
import network
import asyncio
import socket
import random
import framebuf
import rp2
import sys
import time
import ntptime
import ujson

from machine import Pin, I2C
from secret import ssid, password
from ssd1306 import SSD1306_I2C

# Configure display
WIDTH = 128
HEIGHT = 64

i2c = I2C(0, scl = Pin(17), sda = Pin(16), freq=400000)
display = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Configure on-board LED
led = machine.Pin('LED', machine.Pin.OUT)

date_time = time.localtime()
temperature = 0
network_connection = False
display.invert(0) # 0 -> White text on Black BG, 1 -> Black text on White BG
display.contrast(100) # 0 = min, 100 = max

# Temperature Configurations
def get_temp():
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature
  
def readable_temp(temperature):
    formatted_temperature_c = "{:.1f}".format(temperature)
    formatted_temperature_f = "{:.1f}".format((temperature)*(9/5) + 32)
    return [str(formatted_temperature_c), str(formatted_temperature_f)]

def readable_datetime(datetime):
    print("UTC: " + str(datetime))
    local_time = utc_to_local(datetime, -8) # -8  for LosAngeles time zone. 
    dyear, dmonth, dday, dhour, dmin, dsec, dweekday, dyearday = (local_time)
    date_format = "{:02d}/{:02d}/{}" 
    time_format = "{:02d}:{:02d}:{:02d}"
    return [date_format.format(dmonth, dday, dyear), time_format.format(dhour, dmin, dsec)]

def utc_to_local(utc_time, offset):
    """
    Convert UTC time to local time.
    
    :param utc_time: Tuple in the form (year, month, day, hour, minute, second, weekday, yearday)
    :param offset: Timezone offset in hours (can be a float for fractional hours)
    :return: Local time as a tuple
    """
    # Convert UTC tuple to seconds since epoch
    utc_seconds = time.mktime(utc_time)
    
    # Apply the offset (in seconds)
    local_seconds = utc_seconds + int(offset * 3600)
    
    # Convert back to tuple
    local_time = time.localtime(local_seconds)
    return local_time

def display_welcome_text():
    display.text("WELCOME!", 0,21)
    
    display.show()
    display.fill(0)
    time.sleep(3)

def display_temp(temperatures, date_time_texts):
    display.text("Temperature:", 0,0)
    display.text("C: " + temperatures[0],0,11)
    display.text("F: " + temperatures[-1],0,21)
    display.text("Date: " + date_time_texts[0], 0, 31)
    display.text("Time: " + date_time_texts[-1], 0, 41)
    display.text("Server: " + "running" if network_connection else "Server: " + "failed", 0, 51)
    
    display.show()
    display.fill(0)
    
    time.sleep(0.5)

# Init Wi-Fi Interface
def init_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # Connect to your network
    wlan.connect(ssid, password)
    # Wait for Wi-Fi connection
    connection_timeout = 30
    while connection_timeout > 0:
        print(wlan.status())
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        print('Waiting for Wi-Fi connection...')
        time.sleep(1)
    # Check if connection is successful
    if wlan.status() != 3:
        print('Failed to connect to Wi-Fi')
        return False
    else:
        print('Connection successful!')
        network_info = wlan.ifconfig()
        print('IP address:', network_info[0])
        return True

def generate_json_string(temp, date_time):
    json_data = {
        "temperature": temp,
        "timezone": "UTC",
        "year": date_time[0],
        "month": date_time[1],
        "day": date_time[2],
        "hour": date_time[3],
        "minute": date_time[4],
        "second": date_time[5],
        "weekday": date_time[6],  # 0 = Monday, 6 = Sunday
        "yearday": date_time[7],  # Day of the year
    }
    return ujson.dumps(json_data)
    

# Asynchronous function to handle client's requests
async def handle_client(reader, writer):
    global state
    global temperature
    global date_time
    
    print("Client connected")
    request_line = await reader.readline()
    print('Request:', request_line)
    
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass
    
    # Generate response
    response = generate_json_string(temperature, date_time)

    # Send the HTTP response and close the connection
    writer.write('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
    writer.write(response)
    await writer.drain()
    await writer.wait_closed()
    print('Client Disconnected')
    
    
async def temperature_task():
    while True:
        global temperature
        global date_time
        new_temp = get_temp()
        temperature = new_temp 
        date_time = time.localtime()
        temperatures = readable_temp(new_temp)
        readable_date_time = readable_datetime(date_time)
        print(temperatures[0] + " " + temperatures[-1] + " " + readable_date_time[0] + " " + readable_date_time[-1])
        display_temp(temperatures, readable_date_time)
        await asyncio.sleep(1)

async def main():
    global network_connection 
    
    asyncio.create_task(temperature_task())    
    
    connection = init_wifi(ssid, password)
    
    # Start the server and run the event loop
    if connection == True:
        ntptime.settime()
        network_connection = connection
        print('Setting up server')
        server = asyncio.start_server(handle_client, "0.0.0.0", 80)
        asyncio.create_task(server)

# Function calls:

display_welcome_text()

# Create an Event Loop
loop = asyncio.get_event_loop()
# Create a task to run the main function
loop.create_task(main())

try:
    # Run the event loop indefinitely
    loop.run_forever()
except Exception as e:
    print('Error occured: ', e)
except KeyboardInterrupt:
    print('Program Interrupted by the user')