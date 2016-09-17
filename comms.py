import time
import struct
import serial

ser = serial.Serial( 
   port='/dev/ttyAMA0',
   baudrate = 115200,
   timeout= 1
)

input = " "

while True:
	if (ser.inWaiting()>0):	
		bytes = ser.read()
		print repr(bytes)
		print "~"

   
