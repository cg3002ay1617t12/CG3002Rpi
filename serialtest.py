import time
import serial

ser = serial.Serial( 
   port='/dev/ttyAMA0',
   baudrate = 115200,
   timeout=20
)

counter=0
          
while 1:
   ser.write('Write counter: %d \n'%(counter))
   time.sleep(5)
   counter += 1
