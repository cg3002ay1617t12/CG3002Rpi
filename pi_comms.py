import serial
import struct
import time
import heapq
import binascii

#RECEIVE VARIABLES
CurrMode = 0
packet_type = 0 #For packet handling
packet_seq_RX = 0 
data = 0 
component_ID = 0

ser = serial.Serial(port ='/dev/ttyAMA0', baudrate = 115200, timeout = 3)

incomingByte = 0 
dataIndex = 8 #For payload
crcData = 0 
rxCrcIndex = 14
readStatus = False

#SEND VARIABLES
createQueue = 1 
txCrcIndex = 12
protected_flag = 0 #1 means protect it, 0 means can override
packet_type_TX = 44 #PKT_TYPE IS DATA TO SEND
packet_seq_TX = 0 
component_ID_TX = 12
data_TX = 277

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
	if ser.inWaiting()>0:
		readStatus = True
		incomingByte = ser.read() 
		if CurrMode == 0: 
			incomingByte = ord(incomingByte)
			if incomingByte == 60:
				CurrMode = 1
				print("Recieved Start")

		elif CurrMode == 1:
			incomingByte = ord(incomingByte)
			if incomingByte == 40:
				print("Recieved HELLO")
				packet_type = 1 
				CurrMode = 7
			elif incomingByte == 41:
				print("Recieved ACK")
				packet_type = 2
				CurrMode = 3
			elif incomingByte == 42:
				print("Recieved NACK")
				packet_type = 3
				CurrMode = 3
			elif incomingByte == 43:
				print("Recieved PROBE")
				packet_type = 4
				CurrMode = 3
			elif incomingByte == 44:
				print("Recieved REQ")
				packet_type = 5
				CurrMode = 3
			elif incomingByte == 45:
				print("Recieved DATA")
				packet_type = 6
				CurrMode = 3
			else:
				CurrMode = 8
				print("CORRUPT")
			
		elif CurrMode == 3 :
			incomingByte = ord(incomingByte)
			global packet_seq_RX
			print("Payload_seq")
			if packet_seq_RX == 0: 
				CurrMode = 8
				print("CORRUPT")
			else: 
				CurrMode = 4
				packet_seq_RX = not packet_seq_RX
		
		elif CurrMode == 4 :
			incomingByte = ord(incomingByte)
			component_ID = incomingByte
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
			print("crc")
			if incomingByte == 1: 
				CurrMode = 7 
				crcData = incomingByte
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
				print(data)
				print(crcData)
				readStatus = False
				if packet_type ==1 or packet_type ==6:
					handling_packets()
		elif CurrMode == 8:
			print("Handling Corrupt Packet")
			CurrMode = 0
			readStatus = False

def send(packet_type_S, component_ID_S, data_S): 
	global packet_seq_TX
	global packet_type_TX
	global component_ID_TX
	global data_TX

	#Storing previous packet so it will not be overwritten
	packet_type_TX = packet_type_S
	component_ID_TX = component_ID_S
	data_TX = data_S

	ser.write("<")
	ser.write(chr(packet_type_S))
	ser.write(chr(packet_seq_TX))
	ser.write(chr(component_ID_S))
	ser.write(convert(data_S))
	ser.write("1")
	ser.write(">")
	#protected_flag = 1 

def handling_packets(): 
	global packet_type
	global packet_seq_TX
	global packet_type_TX
	global component_ID_TX
	global data_TX

	if packet_type == 1: #(HELLO RECEIVED) send hello back
		#if protected_flag = 0: 
		ser.write("<")
		ser.write("(") 
		ser.write(">")
		#protected_flag = 1 
		#else: 
		#	queueData = {'p_type': 40, 'com_id' : -1 , 'p_data' : -1} 
		#	q.push(queueData, 1)

	#elif packet_type == 2: #(ACK RECEIVED) send ack with pkt_seq, set protected flag down, inverse pkt_seq and send next)
	#	packet_seq_TX = not packet_seq_TX
	#	protected_flag = 0
	#	send(")", packet_seq_TX, component_ID_TX, data_TX) #Send ACK
		#Send next by lowering protected_flag so send can be successful  

	#elif packet_type == 3: #(NACK RECEIVED) resent packet
	#	if protected_flag == 0: 
	#		send(packet_type_TX, component_ID_TX, data_TX)
	#	else: 
	#		queueData = {'p_type': packet_type_TX, 'com_id' : component_ID_TX, 'p_data' : data_TX} 
	#		q.push(queueData, 1)

	#elif packet_type == 4: #(PROBE RECEIVED) send back ack followed by pkt_seq
	#	if protected_flag == 0:
	#		send(")", component_ID_TX, data_TX)
	#	else:
	#		queueData = {'p_type': 41, 'com_id' : component_ID_TX , 'p_data' : data_TX} 
	#		q.push(queueData, 1)

	elif packet_type == 6: #(DATA RECEIVED) send ack back with next pkt_seq
		#if protected_flag == 0:
		send(")", component_ID_TX, data_TX)
		#else:
		#	queueData = {'p_type': 41, 'com_id' : component_ID_TX , 'p_data' : data_TX}
		#	q.push(queueData, 1) 

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
	#if createQueue: 
	#	q = PriorityQueue() 
	#	createQueue = 0 
	#How to create this queue outside? 

	read()

	#if protected_flag == 0: 
	#	toSend = q.pop() 
	#	if toSend.get('p_type') == 40:   #Special case for re-sending HELLO packet 
	#		ser.write("<")
	#		ser.write("(") 
	#		ser.write(">")
	#		protected_flag = 1 
	#	else: 
	#		send(toSend.get('p_type'), toSend.get('com_id'), toSend.get('p_data'))
