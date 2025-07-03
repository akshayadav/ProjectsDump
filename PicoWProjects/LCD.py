import LCD_1inch8
import time

import network
import time
from secret import ssid, password
import socket

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)
while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect:")
    time.sleep(1)
 
# Should be connected and have an IP address
wlan.status() # 3 == success
wlan.ifconfig()

# initialize LCD
LCD = LCD_1inch8.LCD_1inch8()    
#color BRG
LCD.fill(LCD.WHITE)
LCD.show()

if __name__=='__main__':
    
    print("running main")
    
    while True:
        print("running main loop")

    