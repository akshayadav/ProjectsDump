from time import sleep
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C

# Initialize I2C (adjust pins as needed)
i2c = I2C(0, sda=Pin(1), scl=Pin(2), freq=400000)

# Initialize OLED (128x64 is common, but use your display's resolution)
oled = SSD1306_I2C(128, 64, i2c)

# Clear the display
oled.fill(0)

# Write text to the display
oled.text("Hello, World!", 0, 0)
oled.text("Pico W OLED", 0, 10)

# Update the display to show the text
oled.show()



# Initialize PIR sensor on GPIO 0
pir = Pin(0, Pin.IN)

print("PIR sensor test")
while True:
    if pir.value() == 1:
        print("Motion detected!")
        # Clear the display
        oled.fill(0)

        # Write text to the display
        oled.text("Motion Detected!", 0, 0)

        # Update the display to show the text
        oled.show()
        sleep(1)  # LED stays on for 1 second
        
    else:
        print("No motion")
        
        oled.fill(0)

        # Write text to the display
        oled.text("No Motion", 0, 0)

        # Update the display to show the text
        oled.show()
    sleep(0.1)  # Short delay to avoid flooding the console