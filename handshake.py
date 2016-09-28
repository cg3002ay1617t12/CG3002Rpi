import serial
import time

def handshake(): 
	ser = serial.Serial(‘/dev/ttyAMA0’, 9600, timeout=1)
	sleep(2)
	receive = 0 

	while receive != 1: 
		ser.write(chr('\x07')) #Keep sending bell
		sleep(2)
		if ser.read(1) == 'ACK' #ACK received
			print 'ACK received'
			receive = 1
			ser.write(chr('\x06')) #Send ACK back 
			sleep(2)
			if ser.read(1) == 'ACK'
				print 'Handshake established'

	ser.close()



