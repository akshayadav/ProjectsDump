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
import utime
import ntptime
import ujson
import math

from machine import Pin, I2C, RTC
from secret import ssid, password
from ssd1306 import SSD1306_I2C

# Configure display
WIDTH = 128
HEIGHT = 64

i2c = I2C(0, scl = Pin(17), sda = Pin(16), freq=400000)

# Configure on-board LED
led = machine.Pin('LED', machine.Pin.OUT)

oled = SSD1306_I2C(128, 64, i2c)

# Clock parameters (moved slightly to the left)
CENTER_X = 48
CENTER_Y = 32
CLOCK_RADIUS = 30

# Hand lengths
HOUR_HAND = 15
MINUTE_HAND = 20
SECOND_HAND = 25

# Connect to Wi-Fi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    print("Connecting to Wi-Fi...")
    while not wlan.isconnected():
        utime.sleep(1)
        print("Still connecting...")
    
    print("Connected to Wi-Fi!")
    print("IP Address:", wlan.ifconfig()[0])

# Synchronize time with NTP server
def sync_time():
    try:
        print("Synchronizing time with NTP server...")
        ntptime.settime()  # Sync time with NTP server (UTC)
        print("Time synchronized!")
    except Exception as e:
        print("Failed to synchronize time:", e)

# Draw clock face with hour markers
def draw_clock_face():
    # Draw clock outline
    for angle in range(0, 360, 30):  # Hour markers every 30 degrees
        rad = math.radians(angle)
        x_outer = CENTER_X + int(math.cos(rad) * CLOCK_RADIUS)
        y_outer = CENTER_Y + int(math.sin(rad) * CLOCK_RADIUS)
        x_inner = CENTER_X + int(math.cos(rad) * (CLOCK_RADIUS - 3))
        y_inner = CENTER_Y + int(math.sin(rad) * (CLOCK_RADIUS - 3))
        oled.line(x_inner, y_inner, x_outer, y_outer, 1)

# Draw clock hands based on angles
def draw_hand(angle, length):
    rad = math.radians(angle - 90)  # Offset by -90° to start at the top of the clock face
    x_end = CENTER_X + int(math.cos(rad) * length)
    y_end = CENTER_Y + int(math.sin(rad) * length)
    oled.line(CENTER_X, CENTER_Y, x_end, y_end, 1)

# Display date on the right side of the screen
def display_date(current_time):
    year = current_time[0]
    month = current_time[1]
    day = current_time[2]
    
    oled.text(f"{year}", 90, 10)       # Year at the top-right corner
    oled.text(f"{month:02d}/{day:02d}", 90, 25)  # Month/Day below year

# Main loop to update the clock every second
def run_clock():
    rtc = RTC()
    
    while True:
        oled.fill(0)  # Clear display
        
        # Get current time from RTC (adjust for PST: UTC-8)
        current_time = rtc.datetime()
        hours = (current_time[4] - 8) % 12 or 12  # Convert to PST and handle 12-hour format
        minutes = current_time[5]
        seconds = current_time[6]
        
        # Calculate angles for hands
        second_angle = seconds * 6                # Each second is 6 degrees (360/60)
        minute_angle = minutes * 6 + seconds / 10 # Each minute is 6 degrees + fractional seconds
        hour_angle = hours * 30 + minutes / 2     # Each hour is 30 degrees + fractional minutes
        
        # Draw clock face and hands
        draw_clock_face()
        draw_hand(hour_angle, HOUR_HAND)         # Hour hand
        draw_hand(minute_angle, MINUTE_HAND)     # Minute hand
        draw_hand(second_angle, SECOND_HAND)     # Second hand
        
        # Center dot for aesthetics
        oled.pixel(CENTER_X, CENTER_Y, 1)
        
        # Display date on the right side of the screen
        display_date(current_time)
        
        oled.show()                              # Update display
        
        utime.sleep(1)                           # Wait for one second

# Main function to set up and run the clock
def main():
    connect_to_wifi()   # Connect to Wi-Fi network
    sync_time()         # Synchronize time with NTP server
    
    run_clock()         # Start the clock

if __name__ == "__main__":
    main()