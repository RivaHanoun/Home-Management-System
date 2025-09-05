# Building Management System (BMS)

A Raspberry Pi–based Building Management System that monitors and controls environmental factors such as lighting, HVAC, fire alarms, and security.  
This project was developed for EECS 113 at UC Irvine.

## Demo Video
👉 [Link to Demo Video](https://youtu.be/myGDymr_ii4)

## Features
- **Ambient Lighting Control**: Uses PIR sensor to detect motion and turn lights on/off with a 10s timeout.  
- **HVAC System**:  
  - Reads temperature via DHT11 sensor every second.  
  - Pulls humidity data from the CIMIS API.  
  - Calculates a *weather index* (feels-like temperature).  
  - Uses hysteresis (±3°F) to prevent constant toggling between AC (blue LED + fan motor) and heater (red LED).  
- **Fire Alarm**: Activates if weather index exceeds 95°F, triggering HVAC shutdown, door/window opening, flashing lights, and LCD emergency message.  
- **Security System**:  
  - Door/window button toggles open/closed state.  
  - HVAC is disabled when door/window is open.  
  - LCD shows warnings for 3 seconds when status changes.  
- **LCD Display**: Shows current and desired temperature, weather index, HVAC status, lighting status, and door/window status.  

## Hardware Components
- Raspberry Pi (GPIO controlled)  
- DHT11 Temperature Sensor  
- PIR Motion Sensor  
- CIMIS API for humidity data  
- LCD Display  
- LEDs (Green, Blue, Red)  
- Push Buttons (temperature up/down, door/window toggle)  
- L293D motor driver + fan attachment  

## How It Works
1. **Lighting**: PIR detects movement → Green LED turns on → Off after 10s of inactivity.  
2. **Temperature & Humidity**:  
   - DHT11 provides temperature.  
   - CIMIS API provides humidity.  
   - Weather Index = `temperature + 0.05 * humidity`.  
3. **HVAC Logic**:  
   - AC (Blue LED + Fan Motor) turns on if `weather_index > desired_temp + 3`.  
   - Heater (Red LED) turns on if `weather_index < desired_temp - 3`.  
   - HVAC turns off if door/window is open.  
4. **Fan Control**: Fan motor runs *only when AC is active*. Heater mode and HVAC-off states leave fan powered down.  
5. **Fire Alarm**: Activates if `weather_index > 95`.  
6. **LCD**: Displays system status in real time. 

## Setup Instructions
1. Connect components to Raspberry Pi GPIO pins as described in the [Project Report.pdf](https://github.com/user-attachments/files/22182988/Project.Report.pdf).  
2. Install required Python libraries (e.g., `Adafruit_DHT`, `requests`, `RPi.GPIO`).  
3. Run the main program
4. Adjust desired temperature with increment/decrement buttons.
5. Test system features (lights, HVAC, fan, fire alarm, security) with real-world inputs.
