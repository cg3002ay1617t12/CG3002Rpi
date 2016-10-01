import serial
import struct
import time
import heapq
import binascii

#RECEIVE VARIABLES
CurrMode = 0
packet_type = 0 #For packet handling
data = "" 
component_ID = 0
payload_length = 0 
acc_x = 0 
acc_y = 0 
acc_z = 0 

ser = serial.Serial(port ='/dev/ttyAMA0', baudrate = 115200, timeout = 3)

incomingByte = 0 
dataIndex = 0 #For payload
crcIndex = 2 
crcData = 0 
rxCrcIndex = 14
readStatus = False
payload_final = 0 
crc_final = 0 

#SEND VARIABLES
createQueue = 1 
txCrcIndex = 12

#SHARED VARIABLES
crcPoly = "100000111"

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
	data_string = ''.join(toSend)
	return data_string
	
def read(): 
	global crcData
	global CurrMode
	global packet_type
	global dataIndex
	global data
	global crcIndex
	global payload_final
	global payload_length
	global crc_final

	if ser.inWaiting()>0:
		readStatus = True
		incomingByte = ser.read()
		print incomingByte 
		if CurrMode == 0: 
			incomingByte = ord(incomingByte)
			if incomingByte == 60:
				CurrMode = 1
				print("Recieved Start")

		elif CurrMode == 1:
			incomingByte = ord(incomingByte)
			if incomingByte == 48:
				print("Recieved HELLO")
				packet_type = 1 
				CurrMode = 7
			elif incomingByte == 49:
				print("Recieved ACK")
				packet_type = 2
				CurrMode = 7
			elif incomingByte == 50:
				print("Recieved DATA")
				packet_type = 6
				CurrMode = 2
			else:
				CurrMode = 8
				print("CORRUPT")

		elif CurrMode == 2 :
			incomingByte = ord(incomingByte)
			component_ID = incomingByte
			print("Component_ID")
			if incomingByte >0 and incomingByte <42: 
				CurrMode = 3 
			else:
				CurrMode = 8
				print("CORRUPT")

		elif CurrMode == 3 :
			incomingByte = ord(incomingByte)
			payload_length = incomingByte
			print("Payload Length")
			if incomingByte >-1 and incomingByte <58: 
				CurrMode = 5
				dataIndex = payload_length 
			else:
				CurrMode = 8
				print("CORRUPT")
		
		elif CurrMode == 5 :
			#incomingByte = ord(incomingByte)
			#incomingByte = int(incomingByte)			
			print("Payload")
			if dataIndex > -1: 
				data = data + incomingByte
				dataIndex = dataIndex-1 
				if dataIndex == 0:
					print (data)
					payload_final = data 
					data = ""
					dataIndex = -1
					CurrMode = 6
	
		elif CurrMode == 6 :
			incomingByte = ord(incomingByte)
			print("crc")
			print incomingByte
			if crcIndex > -1: 
				if incomingByte == 48: 
					crcData = crcData + incomingByte
					crcIndex = crcIndex -1
				 	if crcIndex == 0:
				 		crc_final = crcData
				 		crcData = 0 
				 		crcIndex = 2 
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
				print("Successfully")
				CurrMode = 0
				print(payload_length)
				print(payload_final)
				print(crc_final)
				readStatus = False
				if packet_type ==1 or packet_type ==6:
					handling_packets()
				if packet_type == 6:
					split_data(payload_final)

		elif CurrMode == 8:
			print("Handling Corrupt Packet")
			CurrMode = 0
			readStatus = False

def handling_packets(): 
	if packet_type == 1: 
		print ("Sending HELLO Packet")
		ser.write("<")
		ser.write("(") 
		ser.write(">")
		ser.flush()

	elif packet_type == 6: 
		print("Sending ACK Packet")
		ser.write("<")
		ser.write("1")
		ser.write(">")
		ser.flush()

def split_data(data): 
	global acc_x
	global acc_y
	global acc_z

	data = data.strip()
	values = []
	values = data.split(',')
	if len(values) == 3: #ACCELEROMETER
		acc_x = values[0] 
		acc_y = values[1]
		acc_z = values[2]
		print(acc_x)
		print(acc_y)
		print(acc_z)

def txCRC():
	global packet_type
	global packet_seq_TX
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

while 1:
	read()