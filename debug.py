import time
import struct
import serial

ser = serial.Serial( 
   port='/dev/ttyAMA0',
   baudrate = 115200,
   timeout= 1
)

input = " "
          
#   input = raw_input("Please enter msg to send \n");
#   if input == "quit" or input == "exit":
#       break;
#   print "Sending out " + input 
#   ser.write(struct.pack('!B', 245));
try:
    while 1:
	if (ser.inWaiting()>0):
        	response = ser.readline()
        	print response
except KeyboardInterrupt:
    print "shutting down"
    ser.close()
except IOError:
    print "IO error"
    ser.close()
