import time
import serial

ser = serial.Serial( 
   port='/dev/ttyAMA0',
   baudrate = 115200,
   timeout= 3
)

input = " "
          
while 1:
   input = raw_input("Please enter msg to send \n");
   if input == "quit" or input == "exit":
       break;
   print "Sending out " + input 
   ser.write(input);