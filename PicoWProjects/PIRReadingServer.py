import network
import socket
import time
from machine import Pin, ADC
from secret import ssid,password

wlan = network.WLAN(network.STA_IF)


# Define the PIR sensor input pin
pir_pin = Pin(22, Pin.IN)

# Define the LED pin (optional, for visual feedback)
led = machine.Pin("LED", machine.Pin.OUT)

# Flags to indicate motion detection state
motion_detected = False

# motion_stopped_printed = False

# Callback function to handle motion detection
def pir_interrupt(pin):
    global motion_detected
    if pin.value() == 1:  # Rising edge (motion detected)
        motion_detected = True
        led.on()  # Turn on the LED
        print("Motion Detected")
    else:  # Falling edge (motion stopped)
        motion_detected = False
        led.off() # Turn off the LED
        print("No Motion")

# Configure the interrupt on the PIR pin for both rising and falling edges
pir_pin.irq(trigger=(Pin.IRQ_RISING | Pin.IRQ_FALLING), handler=pir_interrupt)

def setupWlan():
    wlan.active(False)
    time.sleep(2)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    # Wait for connect or fail
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)
    
    # Handle connection error
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0] )

setupWlan()

# Open socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1] # See more info here: https://docs.micropython.org/en/latest/library/socket.html

s = socket.socket()
s.bind(addr)
s.listen(0) # s.listen(1)

print('listening on', addr)

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        print(request)
        # Do not unpack request
        # We reply to any request the same way
        # Generate 3 values to send back
        #r = random.randint(0,255)
        #g = random.randint(0,255)
        #b = random.randint(0,255)
        # Join to make a simple string with commas as separators
        # rgb = str(r) + "," + str(g) + ","+str(b)
        
        response = "MOTION" if motion_detected else "NOMOTION" # This is what we send in reply

        cl.send(response)
        print("Sent:" + response)
        cl.close()

    except OSError as e:
        cl.close()
        print('server : connection closed due to error')
        
#     except KeyboardInterrupt:
#         print("Keyboard interrupt")
#         pir_pin.irq(trigger=0)  # Disable the interrupt
#         led.off()  # Turn off the LED


