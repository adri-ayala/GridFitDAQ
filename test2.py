import serial
import time
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid


# Configuration
SERIAL_PORT = 'COM3'  # Adjust to your port
BAUD_RATE = 115200

client = MongoClient('mongodb+srv://adri-ayala:Pickles254@gridfit.szhbvt2.mongodb.net/?retryWrites=true&w=majority&appName=GridFit')
db = client['GridFit']
readings_collection = db['Session']
summary_collection = db['UserStats']
RESISTOR_OHMS = 0.10

def initialize_daq(ser):
    """Send initialization commands to the DI-1100."""
    commands = [

        'stop', # Stop any ongoing acquisition
        'clist',        #clear collected list
        'encode 0',     # Set binary output mode
        'ps 0',         # Set packet size to small
        'slist 0 1',    # Configure scan list: position 0, analog channel 0
        'srate 1000',  # Set sample rate
        'start'         # Start acquisition
    ]
    for cmd in commands:
        ser.write((cmd + '\r').encode())
        time.sleep(0.1)  # Brief pause between commands

def read_voltage(ser):
    """Read and decode voltage data from the DI-1100."""
    while True:
        data = ser.read(2)  # Read 2 bytes
        if len(data) == 2:
            raw_value = int.from_bytes(data, byteorder='little') & 0x0FFF
            voltage = (raw_value / 4095) * 10
            print(f"Raw value: {raw_value}, Voltage: {voltage:.3f} V")
        time.sleep(1)

def main():
    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to DAQ on {SERIAL_PORT}...")
            initialize_daq(ser)
            read_voltage(ser)
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")

if __name__ == "__main__":
    main()

