import serial
import struct
import time
import heapq
import binascii

#enum {0, 1, 2, 3, 4 , 5, 6, 7, 8 }

CurrMode = 0
packet_type = 0 #save the type of packet

booted = '0'
bufferSize = 0

ser = serial.Serial(port ='/dev/ttyAMA0', baudrate = 115200, timeout = 3)

incomingByte = 0
	
packet_size = 0
packet_size_count = 0
	
packet_seq = '0'

dataSize = [] 
data = 0 
numComponent = 0 # MAX 10
componentID = 0
componentFlag = '0'
componentTemp = 0

dataIndex = 8 
payloadData = 1 # need to findout why is it it bugging out

crcSize = 4
crcIndex=0
crcData = [] # need to findout why is it it bugging out
crcPoly = "100000111"
txCrcIndex = 12
rxCrcIndex = 14
	
readStatus = False
flag = 0

class PriorityQueue:
	def __init__(self):
		self._queue = []
		self._index = 0

	def push(self, item, priority):
		heapq.heappush(self._queue, (priority, self._index, item))
		self._index += 1

	def pop(self):
		return heapq.heappop(self._queue)[-1]

def convert(number):
	count = 8
	toSend = [] 
	while (count > 0):
		count = count - 1
		if number>=255:
			number = number - 255
			toSend.append(struct.pack('!B', 255))
		else: 
			toSend.append(struct.pack('!B', number))
			number = 0
	return toSend
	

def read(): 
	global CurrMode
	if ser.inWaiting()>0:
		#print "wait > 0"
		readStatus = True
		#while readStatus:
		#print("enter read mode")
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
			incomingByte = ord(incomingByte)
			global packet_seq
			print("Payload_seq")
			if packet_seq == 0: 
				CurrMode = 8
				print("CORRUPT")
			else: 
				CurrMode = 4
				packet_seq = not packet_seq
		
		elif CurrMode == 4 :
			incomingByte = ord(incomingByte)
			component_id = incomingByte
			print("component_id")
			if incomingByte >0 and incomingByte <41: 
				CurrMode = 5 
			else:
				CurrMode = 8
				print("CORRUPT")
		
		elif CurrMode == 5 :
			incomingByte = ord(incomingByte)
			incomingByte = int(incomingByte)
			global dataIndex
			global data
			print("payload")
			if dataIndex > -1: 
				data = data + incomingByte
				dataIndex = dataIndex-1 
				if dataIndex == 0:
					CurrMode = 6
	
		elif CurrMode == 6 :
			incomingByte = ord(incomingByte)
			incomingByte = int(incomingByte)
			global crcSize
			global crcIndex
			print("crc")
			if incomingByte == 1: 
				CurrMode = 7 
			else:
				CurrMode = 8 
				print("CORRUPT")

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
				#handling packets funct here
		
		elif CurrMode == 8:
			print("Handling Corrupt Packet")
			CurrMode = 0
			readStatus = False

def send(): 
	global packet_seq
	global packet_type
	global component_id
	global data
	ser.write("<")
	ser.write(packet_type)
	ser.write(packet_seq)
	ser.write(component_id)
	ser.write(data)
	ser.write(1)
	ser.write(">")

def handling_packets(): 
	global packet_type
	if packet_type == 3: #PROBE
		send()


def txCRC():
	global packet_type
	global packet_seq
	global component_id
	global data
	toBeDivided = []
	toBeDivided.append(format(60, "08b")) #START
	toBeDivided.append(format(11, "08b")) #PACKET_TYPE
	toBeDivided.append(format(22, "08b")) #PACKET_SEQ
	toBeDivided.append(format(44, "08b")) #COMPONENT_ID
	toBeDivided.append(format(65, "064b")) #DATA
	toBeDivided.append(format(0, "08b")) #PAD 8 ZEROS
	divided_string = ''.join(toBeDivided)
	#print divided_string
	return divided_string

# Returns XOR of 'a' and 'b'
# (both of same length)
def xor(a, b):
	# initialize result
	result = []

	# Traverse all bits, if bits are
	# same, then XOR is 0, else 1
	for i in range(1, len(b)):
		if a[i] == b[i]:
			result.append('0')
		else:
			result.append('1')

	return ''.join(result)

# Performs Modulo-2 division
def mod2div(divident, divisor):

	# Number of bits to be XORed at a time.
	pick = len(divisor)

	# Slicing the divident to appropriate
	# length for particular step
	tmp = divident[0 : pick]

	while pick < len(divident):

		if tmp[0] == '1':

			# replace the divident by the result
			# of XOR and pull 1 bit down
			tmp = xor(divisor, tmp) + divident[pick]

		else:   # If leftmost bit is '0'
			# If the leftmost bit of the dividend (or the
			# part used in each step) is 0, the step cannot
			# use the regular divisor; we need to use an
			# all-0s divisor.
			tmp = xor('0'*pick, tmp) + divident[pick]

		# increment pick to move further
		pick += 1

	# For the last n bits, we have to carry it out
	# normally as increased value of pick will cause
	# Index Out of Bounds.
	if tmp[0] == '1':
		tmp = xor(divisor, tmp)
	else:
		tmp = xor('0'*pick, tmp)

	checkword = tmp
	return checkword

# Function used at the sender side to encode
# data by appending remainder of modular divison
# at the end of data.
def encodeData(data, key):

	l_key = len(key)

	# Appends n-1 zeroes at end of data
	appended_data = data + '0'*(l_key-1)
	remainder = mod2div(appended_data, key)

	# Append remainder in the original data
	codeword = data + remainder
	print("Remainder:")
	print(remainder)
	print("Encoded Data (Data + Remainder Appended):")
	print(codeword)

#q = PriorityQueue() 
#q.push("hello world", 5)
#q.push("this is high priority", 3)
#q.push("second highest", 4)
#q.pop()
#q.pop()
#q.pop()

while 1:
	#read()
	#txCRC()
	#if flag==0:
	#	encodeData(txCRC() ,crcPoly)
	#	flag =1
	read()
