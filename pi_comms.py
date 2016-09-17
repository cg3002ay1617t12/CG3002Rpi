import serial
import time

#enum {0, 1, 2, 3, 4 , 5, 6, 7, 8 }

CurrMode = 0

booted = '0'
bufferSize = 0

ser = serial.Serial(
		port ='/dev/ttyAMA0', 
		baudrate = 57600,
		timeout = 3
)

incomingByte = 0
	  
packet_size = 0
packet_size_count = 0
	  
packet_seq = '0'

numComponent = 0 # MAX 10
componentID = []
componentFlag = '0'
componentTemp = 0

dataIndex = 0 
payloadData = 1 # need to findout why is it it bugging out

crcCount = 4
crcData = 1 # need to findout why is it it bugging out
	  
readStatus = False

def read():
	CurrMode = 0; 
	if ser.inWaiting()>0:
		readStatus = True
		while readStatus:

			incomingByte = ser.read()
			if CurrMode == 0: 
				if incomingByte == 60:
					CurrMode = 1
					print("Recieved Start")

			elif CurrMode == 1:
				if incomingByte == 40:
					print("Recieved ACK")
					CurrMode = 2
				elif incomingByte == 41:
					print("Recieved NACK")
					CurrMode = 2
				elif incomingByte == 42:
					print("Recieved Prob")
					CurrMode = 2
				elif incomingByte == 43:
					print("Recieved Read")
					CurrMode = 2
				elif incomingByte == 44:
					print("Recieved Data")
					CurrMode = 2
				elif incomingByte == 45:
					print("Recieved Request")
					CurrMode = 2
				else:
					CurrMode = 8
					print("CORRUPT")

			elif CurrMode == 2:
				print("Payload_length")
				if packet_size_count == 0:
					packet_size += (incomingByte-48) * 100
					packet_size_count += 1
				elif packet_size_count == 1:
					packet_size += (incomingByte-48) * 10
					packet_size_count += 1
				else:
					packet_size += (incomingByte-48)
					packet_size_count = 0
					CurrMode = 3
					print("DEBUG!!!")
					print(packet_size)
					print("DEBUG!!!")
					dataIndex = packet_size
			
			elif CurrMode == 3 :
				print("Payload_seq")
				if packet_seq == (incomingByte-48): 
					CurrMode = 8
					print("CORRUPT")
				else: 
					CurrMode = 4
					packet_seq = not packet_seq
		
			elif CurrMode == COMPONENT_ID :
				print("component_id")
				if componentFlag == '0': 
					componentTemp += (incomingByte-48)*10
					componentFlag = not componentFlag
				else: 
					componentTemp += (incomingByte-48)
					componentID[numComponent] = componentTemp
					numComponent += 1
					componentTemp = 0
					componentFlag = not componentFlag
		
				if numComponent == 11:
					CurrMode = 8
					print("CORRUPT")
		
				elif incomingByte == 64:
					if componentFlag == '1':
						CurrMode = 8
						print("CORRUPT")
					CurrMode = 5
		
			elif CurrMode == 5 :
				print("payload")
				if dataIndex > -1: 
					payloadData = payloadData + pow(10.0,dataIndex-1) * (incomingByte-48)
					dataIndex = dataIndex - 1
					if dataIndex == 0:
						CurrMode = 6
	
		# need to kiv the different sensors and the number of bytes of data sent respectively
			elif CurrMode == 6 :
				print("crc")
				if crcCount > -1:
					print("~")
					print(incomingByte)
					crcData = crcData + pow(10.0,crcCount-1) * (incomingByte-48)
					print(crcData)
					crcCount = crcCount - 1
					if crcCount == 0:
						crcCount = 4
						CurrMode = 7

	
			elif CurrMode == 7:
				print("terminate")
				if incomingByte != 62 :
					CurrMode = 8
					print("CORRUPT")
					readStatus = False
				else:
					CurrMode = 0;
					print(componentID[0])
					print(payloadData)
					print(crcData)
					readStatus = False
		
			elif CurrMode == 8:
				print("handling corrupt packet")
				CurrMode = 0
				readStatus = False


ser.write("<")
time.sleep(1)
ser.write(",")
time.sleep(1)
ser.write("005")
time.sleep(1)
ser.write("1")
time.sleep(1)
ser.write("01")
time.sleep(1)
ser.write("@")
time.sleep(1)
ser.write("22222")
time.sleep(1)
ser.write("1111")
time.sleep(1)
ser.write(">")

while(True):
   read()
