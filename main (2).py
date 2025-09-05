from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
from time import sleep, strftime
from datetime import datetime
import threading
import RPi.GPIO as GPIO
import time
import Freenove_DHT as DHT

# Constants
MIN_TEMP = 65
MAX_TEMP = 95

# Global variables
current_temp = 0
humidity = 0
desired_temp = 75  # Initial desired temperature
door_status = "C"
hvac_status = "Off"
light_status = "Off"
weather_index = 0
lock = threading.Lock()

# DHT11 sensor setup
DHTPin = 17 # GPIO 4 for DHT11 data pin
dht = DHT.DHT(DHTPin)

# PIR sensor setup
PIRPin = 18  # GPIO 17 for PIR sensor

# LED setup
LED_PIN_GREEN = 4  # Green LED for ambient light
LED_PIN_RED = 27    # Red LED for heater
LED_PIN_BLUE = 22   # Blue LED for AC

# Button setup
BUTTON_INC = 25  # Button to increase desired temperature
BUTTON_DEC = 16  # Button to decrease desired temperature
BUTTON_DOOR_WINDOW = 23  # Button for door/window status

CIMIS_API_URL = "http://et.water.ca.gov/api/data"  # CIMIS API URL
CIMIS_STATION_ID = "75"   # CIMIS Station ID for Irvine 
CIMIS_API_KEY = "73a320c8-a6cc-497c-ad7f-a3b62cd02866"

# L293D motor driver setup
MOTOR_PIN_IN1 = 24  # GPIO pin to control IN1
MOTOR_PIN_IN2 = 26  # GPIO pin to control IN2
MOTOR_PIN_VSS = 5   # GPIO pin to control VSS 

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIRPin, GPIO.IN)
GPIO.setup(LED_PIN_GREEN, GPIO.OUT)
GPIO.setup(LED_PIN_RED, GPIO.OUT)
GPIO.setup(LED_PIN_BLUE, GPIO.OUT)
GPIO.setup(BUTTON_INC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_DEC, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_DOOR_WINDOW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MOTOR_PIN_IN1, GPIO.OUT)  
GPIO.setup(MOTOR_PIN_IN2, GPIO.OUT)
GPIO.setup(MOTOR_PIN_VSS, GPIO.OUT)  

# Initialize LCD
PCF8574_address = 0x27  # I2C address of PCF8574 chip
PCF8574A_address = 0x3F  # I2C address of PCF8574A chip

# Create PCF8574 GPIO adapter.
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print('I2C Address Error!')
        exit(1)

# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4, 5, 6, 7], GPIO=mcp)
mcp.output(3, 1)  # LCD backlight
lcd.begin(16, 2)  # Set # of LCD lines/columns

# Functions to handle button presses
def button_inc_callback(channel):
    global desired_temp
    with lock:
        if desired_temp < MAX_TEMP:
            desired_temp += 1

def button_dec_callback(channel):
    global desired_temp
    with lock:
        if desired_temp > MIN_TEMP:
            desired_temp -= 1

def button_door_window_callback(channel):
    global door_status, hvac_status
    with lock:
        if door_status == "C":
            door_status = "O"
            hvac_status = "Off"
            display_message("Window/Door O", "HVAC halted", 3)
        else:
            door_status = "C"
            display_message("Window/Door C", "HVAC on", 3)

# Setup event detection for buttons
GPIO.add_event_detect(BUTTON_INC, GPIO.FALLING, callback=button_inc_callback, bouncetime=300)
GPIO.add_event_detect(BUTTON_DEC, GPIO.FALLING, callback=button_dec_callback, bouncetime=300)
GPIO.add_event_detect(BUTTON_DOOR_WINDOW, GPIO.FALLING, callback=button_door_window_callback, bouncetime=300)

def get_cimis_humidity():
    global humidity
    params = {
        'appKey': CIMIS_API_KEY,
        'targets': CIMIS_STATION_ID,
        'dataItems': 'hly-rel-hum',
        'unitOfMeasure': 'M'
    }
    response = requests.get(CIMIS_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'Data' in data and 'Providers' in data['Data'] and len(data['Data']['Providers']) > 0:
            records = data['Data']['Providers'][0]['Records']
            if len(records) > 0:
                humidity = records[-1]['hly-rel-hum']['Value']
    else:
        print("Failed to retrieve CIMIS data")
        
def update_dht11():
    global current_temp, humidity
    while True:
        for _ in range(0, 15):
            chk = dht.readDHT11()
            if chk == dht.DHTLIB_OK:
                break
            time.sleep(0.1)
        with lock:
            current_temp = round(dht.temperature)
            humidity = round(dht.humidity)
        time.sleep(1) 

def update_pir():
    global light_status
    while True:
        if GPIO.input(PIRPin):
            GPIO.output(LED_PIN_GREEN, GPIO.HIGH)
            with lock:
                light_status = "On"
            time.sleep(10)
        else:
            GPIO.output(LED_PIN_GREEN, GPIO.LOW)
            with lock:
                light_status = "Off"
        time.sleep(1)

def calculate_weather_index():
    global weather_index
    while True:
        with lock:
            weather_index = round(current_temp + 0.05 * humidity)
        time.sleep(1)

def control_hvac():
    global hvac_status
    while True:
        with lock:
            weather_index_f = round(weather_index * 9/5 + 32)
            if weather_index_f >= 95:
                GPIO.output(MOTOR_PIN_IN1, GPIO.LOW)  # Turn off motor
                GPIO.output(MOTOR_PIN_IN2, GPIO.LOW)
                GPIO.output(MOTOR_PIN_VSS, GPIO.LOW) 
                hvac_status = "Off"
                while weather_index_f >= 95:
                    display_message("Fire Alarm!", "Evacuate!", 3)
                    GPIO.output(LED_PIN_BLUE, GPIO.HIGH)
                    GPIO.output(LED_PIN_GREEN, GPIO.HIGH)
                    GPIO.output(LED_PIN_RED, GPIO.HIGH)
                    time.sleep(0.5)
                    GPIO.output(LED_PIN_GREEN, GPIO.LOW)
                    GPIO.output(LED_PIN_RED, GPIO.LOW)
                    GPIO.output(LED_PIN_BLUE, GPIO.LOW)
                    time.sleep(0.5)
                continue

            if door_status == "O":
                GPIO.output(LED_PIN_RED, GPIO.LOW)
                GPIO.output(LED_PIN_BLUE, GPIO.LOW)
                GPIO.output(MOTOR_PIN_IN1, GPIO.LOW)  # Turn off motor
                GPIO.output(MOTOR_PIN_IN2, GPIO.LOW)
                GPIO.output(MOTOR_PIN_VSS, GPIO.LOW) 
                hvac_status = "Off"
                continue

            elif weather_index_f >= desired_temp + 3:
                if hvac_status != "AC":
                    hvac_status = "AC"
                    GPIO.output(LED_PIN_RED, GPIO.LOW)
                    GPIO.output(LED_PIN_BLUE, GPIO.HIGH)
                    GPIO.output(MOTOR_PIN_IN1, GPIO.HIGH)  # Turn on motor in one direction
                    GPIO.output(MOTOR_PIN_IN2, GPIO.LOW)
                    GPIO.output(MOTOR_PIN_VSS, GPIO.HIGH) 
                    display_message("AC is on", "", 3)
            if weather_index_f <= desired_temp - 3:
                if hvac_status != "Heat":
                    hvac_status = "Heat"
                    GPIO.output(LED_PIN_RED, GPIO.HIGH)
                    GPIO.output(LED_PIN_BLUE, GPIO.LOW)
                    GPIO.output(MOTOR_PIN_IN1, GPIO.LOW)  # Turn off motor
                    GPIO.output(MOTOR_PIN_IN2, GPIO.LOW)
                    GPIO.output(MOTOR_PIN_VSS, GPIO.LOW)  
                    display_message("Heater is on", "", 3)
            else:
                if hvac_status != "Off":
                    hvac_status = "Off"
                    GPIO.output(LED_PIN_RED, GPIO.LOW)
                    GPIO.output(LED_PIN_BLUE, GPIO.LOW)
                    GPIO.output(MOTOR_PIN_IN1, GPIO.LOW)  # Turn off motor
                    GPIO.output(MOTOR_PIN_IN2, GPIO.LOW)
                    GPIO.output(MOTOR_PIN_VSS, GPIO.LOW)  
                    display_message("HVAC", "Off", 3)
        time.sleep(1)

def display_message(line1, line2, duration):
    lcd.clear()
    lcd.message(line1 + "\n" + line2)
    sleep(duration)
    lcd.clear()

def display_status():
    global current_temp, desired_temp, door_status, hvac_status, light_status, weather_index
    while True:
        current_temp_f = round(current_temp * (9/5) + 32)
        
        line11 = f"{desired_temp}/{current_temp_f}"
        line12 = f"Dr:{door_status}"
        line21 = f"H:{hvac_status}"
        line22 = f"L:{light_status}"
        
        # Calculate spaces to align text
        space1 = 16 - len(line11) - len(line12)
        line1 = line11 + ' ' * space1 + line12
        space2 = 16 - len(line21) - len(line22)
        line2 = line21 + ' ' * space2 + line22
        
        # Update the LCD
        with lock:
            lcd.setCursor(0, 0)
            lcd.message(line1)
            lcd.setCursor(0, 1)
            lcd.message(line2)
        sleep(1)

def main():
    print('Program is starting ...')

    # threads
    threading.Thread(target=update_dht11, daemon=True).start()
    threading.Thread(target=update_pir, daemon=True).start()
    threading.Thread(target=calculate_weather_index, daemon=True).start()
    threading.Thread(target=control_hvac, daemon=True).start()
    display_status()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        lcd.clear()
        GPIO.cleanup()
        print('Program stopped by user')
