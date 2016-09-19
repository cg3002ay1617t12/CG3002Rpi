import serial
import struct
import time

#enum {0, 1, 2, 3, 4 , 5, 6, 7, 8 }

CurrMode = 0
packet_type = 0 #save the type of packet

booted = '0'
bufferSize = 0

ser = serial.Serial(
		port ='/dev/ttyAMA0', 
		baudrate = 115200,
		timeout = 3
)

incomingByte = 0
	  
packet_size = 0
packet_size_count = 0
	  
packet_seq = '0'

dataSize = [] 
data = 0 
numComponent = 0 # MAX 10
componentID = []
componentFlag = '0'
componentTemp = 0

dataIndex = 8 
payloadData = 1 # need to findout why is it it bugging out

crcSize = 4
crcIndex=0
crcData = []# need to findout why is it it bugging out
	  
readStatus = False

def convertAndSend(number, numdigit):
	count = numdigit
	while (count > 0):
		count = count - 1
		if number>=255:
			number = number - 255
			ser.write(struct.pack('!B', 255))
		else: 
			ser.write(struct.pack('!B', number))
			number = 0
	

def read(): 
	global CurrMode
	if ser.inWaiting()>0:
		print "wait > 0"
		readStatus = True
		#while readStatus:
		print("enter read mode")
		incomingByte = ser.read() 
		if CurrMode == 0: 
			incomingByte = ord(incomingByte)
			if incomingByte == 60:
				CurrMode = 1
				print("Recieved Start")

		elif CurrMode == 1:
			incomingByte = ord(incomingByte)
			if incomingByte == 40:
				print("Recieved ACK")
				packet_type = 1 
				CurrMode = 3
			elif incomingByte == 41:
				print("Recieved NACK")
				packet_type = 2
				CurrMode = 3
			elif incomingByte == 42:
				print("Recieved Prob")
				packet_type = 3
				CurrMode = 3
			elif incomingByte == 43:
				print("Recieved Read")
				packet_type = 4
				CurrMode = 3
			elif incomingByte == 44:
				print("Recieved Data")
				packet_type = 5
				CurrMode = 3
			elif incomingByte == 45:
				print("Recieved Request")
				packet_type = 6
				CurrMode = 3
			else:
				CurrMode = 8
				print("CORRUPT")
			
		elif CurrMode == 3 :
			global packet_seq
			print("Payload_seq")
			if packet_seq == 0: 
				CurrMode = 8
				print("CORRUPT")
			else: 
				CurrMode = 4
				packet_seq = not packet_seq
		
		elif CurrMode == 4 :
			print("component_id")
			if incomingByte >0 and incomingByte <41: 
				CurrMode = 5 
			else:
				CurrMode = 8
				print("CORRUPT")
		
		elif CurrMode == 5 :
			global dataIndex
			global data
			print("payload")
			if dataIndex > -1: 
				data = data + incomingByte
				dataIndex = dataIndex-1 
				if dataIndex == 0:
					CurrMode = 6
	
		elif CurrMode == 6 :
			global crcSize
			global crcIndex
			print("crc")
			if crcSize > -1:
				crcData[crcIndex] = incomingByte
				crcIndex = crcIndex+1 
				print(crcData[crcIndex])
				crcSize = crcSize - 1
				if crcSize == 0:
					crcSize = 4
					CurrMode = 7
	
		elif CurrMode == 7:
			incomingByte = ord(incomingByte)
			print("Terminate")
			if incomingByte != 62 :
				CurrMode = 8
				print("CORRUPT")
				readStatus = False
			else:
				CurrMode = 0
				print(data)
				print(crcData[0])
				print(crcData[1])
				print(crcData[2])
				print(crcData[3])
				readStatus = False
					#add switch case (if ack/nack/data received what happens)
					#if packet_type == 1: 
					#	ser.write(40)
					#elif packet_type ==2:
					#	ser.write()
					#elif packet_type ==3:
					#	ser.write()
		
		elif CurrMode == 8:
			print("Handling Corrupt Packet")
			CurrMode = 0
			readStatus = False


while 1:
	read()
