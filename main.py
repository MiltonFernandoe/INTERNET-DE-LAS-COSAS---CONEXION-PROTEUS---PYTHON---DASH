import serial
import time

ser = serial.Serial('COM11', 115200)
time.sleep(2)

while True:
    cmd = input("Escribe 1 (ON) o 0 (OFF): ")

    if cmd == '1':
        ser.write(b'1')
    elif cmd == '0':
        ser.write(b'0')