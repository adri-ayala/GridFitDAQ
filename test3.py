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
CO2_PER_WATT = 0.000707  # kg CO2 saved per watt-hour 

def initialize_daq(ser):
    """Send initialization commands to the DI-1100."""
    commands = [
        'stop',         # Stop any ongoing acquisition
        'clist',        # Clear collected list
        'encode 0',     # Set binary output mode
        'ps 0',         # Set packet size to small
        'slist 0 1',    # Configure scan list: position 0, analog channel 0
#       'slist 1 2',  # Channel 2 (Current)
        'srate 1000',   # Set sample rate
        'start'         # Start acquisition
    ]
    for cmd in commands:
        ser.write((cmd + '\r').encode())
        time.sleep(0.1)

def read_voltage(ser):
    """Read and decode voltage data from the DI-1100."""
    data = ser.read(2)  # Read 2 bytes
    if len(data) == 2:
        raw_value = int.from_bytes(data, byteorder='little') & 0x0FFF
        voltage = (raw_value / 4095) * 10
        return voltage
    return None

def calculate_power(voltage):
    """Calculate power in watts using Ohm's Law: P = V^2 / R."""
    return (voltage ** 2) / RESISTOR_OHMS

def save_session_data(student_id, session_data):
    readings_collection.insert_one(session_data)
    print(f"Session data saved for student {student_id}.")

def update_user_summary(student_id, total_watts, total_co2, session_duration):
    user_summary = summary_collection.find_one({"student_id": student_id})
    
    if user_summary:
        # Update existing user summary
        summary_collection.update_one(
            {"student_id": student_id},
            {
                "$inc": {
                    "total_watts": total_watts,
                    "total_co2": total_co2,
                    "total_duration": session_duration
                }
            }
        )
    else:
        # Create new user summary
        summary_collection.insert_one({
            "student_id": student_id,
            "total_watts": total_watts,
            "total_co2": total_co2,
            "total_duration": session_duration
        })
    print(f"User summary updated for student {student_id}.")

def main():
    student_id = input("Enter student ID: ")
    session_id = str(uuid.uuid4())
    start_time = time.time()

    total_watts = 0
    total_co2 = 0
    voltage_readings = []

    try:
        with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to DAQ on {SERIAL_PORT}...")
            initialize_daq(ser)

            while True:
                voltage = read_voltage(ser)
                
                if voltage is not None:
                    voltage_readings.append(voltage)
                    watts = calculate_power(voltage)
                    total_watts += watts / 3600  # Convert to watt-hours
                    total_co2 += watts * CO2_PER_WATT / 3600  # Convert to kg CO2 saved
                    
                    print(f"Voltage: {voltage:.3f} V, Watts: {watts:.3f} W")

                time.sleep(1)

    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
    except KeyboardInterrupt:
        print("\nSession ended by user.")
        session_duration = time.time() - start_time

        # Save session data
        session_data = {
            "student_id": student_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc),
            "total_watts": total_watts,
            "total_co2": total_co2,
            "session_duration": session_duration,
            "voltage_readings": voltage_readings
        }
        save_session_data(student_id, session_data)

        # Update user summary
        update_user_summary(student_id, total_watts, total_co2, session_duration)

if __name__ == "__main__":
    main()
