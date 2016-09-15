import serial
import time

enum rxMode {READY, PACKET_TYPE, PAYLOAD_LENGTH, PACKET_SEQ, COMPONENT_ID , PAYLOAD, CRC, TERMINATE, CORRUPT }

booted = '0'
bufferSize = 0


def start():

	ser = serial.Serial(‘/dev/ttyAMA0’, 115200, timeout=3)

	incomingByte = 0
	  
	packet_size = 0
	packet_size_count = 0
	  
	packet_seq = '0'

	numComponent = 0 // MAX 10
	componentID[10] = {0}
	componentFlag = '0'
	componentTemp = 0

	dataIndex = 0 
	payloadData = 1 // need to findout why is it it bugging out

	crcCount = 4
	crcData = 1 // need to findout why is it it bugging out
	  
	rxMode CurrMode = READY
	readStatus = False
  
def read(): 
	if ser.in_waiting>0:
		readStatus = True
		while readStatus: 
    	incomingByte = ser.read()
         
	   	if CurrMode == READY: 
	      	if incomingByte == 60:
	              CurrMode = PACKET_TYPE
	              print("Recieved Start")
	       	
	   	elif CurrMode == PACKET_TYPE:
	       	if incomingByte == 40:
	         	print("Recieved ACK")
	           	CurrMode = PAYLOAD_LENGTH
	       	elif incomingByte == 41:
	           	print("Recieved NACK")
	           	CurrMode = PAYLOAD_LENGTH
	      	elif incomingByte == 42:
	           	print("Recieved Prob")
	           	CurrMode = PAYLOAD_LENGTH
	       	elif incomingByte == 43:
	           	print("Recieved Read")
	           	CurrMode = PAYLOAD_LENGTH
	       	elif incomingByte == 44:
	           	print("Recieved Data")
	           	CurrMode = PAYLOAD_LENGTH
	       	elif incomingByte == 45:
	           	print("Recieved Request")
	          	CurrMode = PAYLOAD_LENGTH
	      	else:
	           	CurrMode = CORRUPT
	           	print("CORRUPT")

	   	elif CurrMode == PAYLOAD_LENGTH:
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
	            CurrMode = PACKET_SEQ
	            print("DEBUG!!!")
	            print(packet_size)
	            print("DEBUG!!!")
	            dataIndex = packet_size
	         
	   	elif CurrMode == PACKET_SEQ :
	       	print("Payload_seq")
	      	if packet_seq == (incomingByte-48): 
	        	CurrMode = CORRUPT
	            print("CORRUPT")
	       	else: 
	            CurrMode = COMPONENT_ID
	            packet_seq = !packet_seq
	   
	   	elif CurrMode == COMPONENT_ID :
	        print("component_id")
	      	if componentFlag == '0': 
	            componentTemp += (incomingByte-48)*10
	            componentFlag = !componentFlag
	        else: 
	            componentTemp += (incomingByte-48)
	            componentID[numComponent] = componentTemp
	            numComponent++
	            componentTemp = 0
	            componentFlag = !componentFlag
	         
	       	if numComponent == 11:
	        	CurrMode = CORRUPT
	            print("CORRUPT")
	          
	        elif incomingByte == 64:
	           	if componentFlag == '1':
	              	CurrMode = CORRUPT;
	              	print("CORRUPT")
	            CurrMode = PAYLOAD
	  
	   	elif CurrMode == PAYLOAD :
	        print("payload")
	       	if dataIndex > -1: 
	        	payloadData = payloadData + pow(10.0,dataIndex-1) * (incomingByte-48)
	            dataIndex = dataIndex - 1
	            if dataIndex == 0:
	            	CurrMode = CRC
	            
	        # need to kiv the different sensors and the number of bytes of data sent respectively
	   	elif CurrMode == CRC :
	      	print("crc")
	       	if crcCount > -1:
	           	print("~")
	            print(incomingByte)
	            crcData = crcData + pow(10.0,crcCount-1) * (incomingByte-48)
	            print(crcData)
	            crcCount = crcCount - 1
	            if crcCount == 0:
	           		crcCount = 4
	           		CurrMode = TERMINATE

	            
	   	elif CurrMode == TERMINATE:
	        print("terminate")
	      	if incomingByte != 62 :
	            CurrMode = CORRUPT
	            print("CORRUPT")
	            readStatus = False
	        else:
	            CurrMode = READY;
	            print(componentID[0])
	            print(payloadData)
	            print(crcData)
	            readStatus = False
	         
	   	elif CurrMode == CORRUPT:
	          print("handling corrupt packet")
	          CurrMode = READY
	          readStatus = False

ser.close()
