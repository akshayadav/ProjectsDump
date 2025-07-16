# Program to read RGB values from a local Pico Web Server
# Tony Goodhew 5th July 2022
# Connect to network
import network
import time
from secret import ssid, password
import socket
import machine


# led = machine.Pin('LED', machine.Pin.OUT) #configure LED Pin as an output pin and create and led object for Pin class
led = machine.Pin(21, machine.Pin.OUT)
# while True:
# #     led.value(True)  #turn on the LED
#     led.value(1)
#     time.sleep(1)   #wait for one second
#     led.value(0)
# #     led.value(False)  #turn off the LED
#     time.sleep(1)   #wait for one second

wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect(ssid, password)
# while not wlan.isconnected() and wlan.status() >= 0:
#     print("Waiting to connect:")
#     time.sleep(1)
#  
# # Should be connected and have an IP address
# wlan.status() # 3 == success
# wlan.ifconfig()
# print(wlan.ifconfig())

def setupWlan():
    print("attempting to connect")
    wlan.active(False)
    time.sleep(2)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected() and wlan.status() >= 0:
        print("Waiting to connect:")
        time.sleep(1)
     
    # Should be connected and have an IP address
    wlan.status() # 3 == success
    wlan.ifconfig()
    print(wlan.ifconfig())
    print("done attempting to connect. wlan status: " + str(wlan.status()))

setupWlan()

while True:
    try:
        print(wlan.isconnected())
        print(wlan.status())
        ai = socket.getaddrinfo("10.0.0.212", 80) # Address of Web Server
        addr = ai[0][-1]

        # Create a socket and make a HTTP request
        s = socket.socket() # Open socket
        s.connect(addr)
        s.send("GET Data") # Send request
        ss=str(s.recv(512)) # Store reply
        # Print what we received
        print(ss)
        if ss == "b'MOTION'":
            led.value(1)
            s.close()
            time.sleep(50)
        else:
            led.value(0)
            s.close()
        time.sleep(1)    # wait
    except OSError as e:
        s.close()
        print('client connection closed due to error' + str(e))
        time.sleep(1)
        setupWlan()
        time.sleep(1)
