import serial
ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
ser.open()
try:
	while 1:
		response = ser.readline()
		print response
except KeyboardInterrupt:
	ser.close()
