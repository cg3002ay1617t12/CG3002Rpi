import serial
ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
try:
	while 1:
		if (ser.inWaiting()>0):
			response = ser.read()
			print response
except KeyboardInterrupt:
	ser.close()
