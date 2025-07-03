import machine
import time

# led = machine.Pin('LED', machine.Pin.OUT) #configure LED Pin as an output pin and create and led object for Pin class
led = machine.Pin(21, machine.Pin.OUT)
while True:
#     led.value(True)  #turn on the LED
    led.value(1)
    time.sleep(1)   #wait for one second
    led.value(0)
#     led.value(False)  #turn off the LED
    time.sleep(1)   #wait for one second