import serial, struct, time, heapq, binascii, os, signal

#RECEIVE VARIABLES

class PriorityQueue:
	def __init__(self):
		self._queue = []
		self._index = 0

	def push(self, item, priority):
		heapq.heappush(self._queue, (priority, self._index, item))
		self._index += 1

	def pop(self):
		return heapq.heappop(self._queue)[-1]

class PiComms(object):
	
	rxCrcIndex      = 14
	
	#SEND VARIABLES
	createQueue     = 1 
	txCrcIndex      = 12
	DATA_PIPE          = './data_pipe'
	EVENT_PIPE         = './event_pipe'
	BAUD               = 115200
	SERIAL             = '/dev/ttyAMA0'
	SAMPLES_PER_PACKET = 25

	#SHARED VARIABLES
	crcPoly = "100000111"
	def __init__(self):
		self.pq              = PriorityQueue()
		self.CurrMode        = 0
		self.packet_type     = 0 #For packet handling
		# data               = 0 
		self.component_ID    = 0
		self.ser             = serial.Serial(port =PiComms.SERIAL, baudrate = PiComms.BAUD, timeout = 3)
		self.data            = 0
		self.packet_seq_RX   = 48
		
		# self.incomingByte  = 0 
		self.crcData         = 0 
		self.readStatus      = False
		self.protected_flag  = 0 #1 means protect it, 0 means can override
		
		self.packet_seq_TX   = 0 
		self.packet_type_TX  = 44 #PKT_TYPE IS DATA TO SEND
		self.component_ID_TX = 12
		self.data_TX         = 277
		self.dataIndex       = 8 #For payload
		self._buffer         = []

		if not os.path.exists(PiComms.DATA_PIPE):
			os.mkfifo(PiComms.DATA_PIPE)

		self.pipe_out = os.open(PiComms.DATA_PIPE, os.O_WRONLY)
		fpid          = open('./pid', 'r')
		self.pid      = fpid.read()
		fpid.close()

	def convert(self, number):
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
		
	def read(self): 
		# global self.crcData, self.CurrMode, self.packet_type, PiComms.dataIndex, data, packet_seq_RX	
		if self.ser.inWaiting()>0:
			self.readStatus = True
			self.incomingByte = self.ser.read()
			print self.incomingByte 
			if self.CurrMode == 0: 
				self.incomingByte = ord(self.incomingByte)
				if self.incomingByte == 60:
					self.CurrMode = 1
					print("Recieved Start")

			elif self.CurrMode == 1:
				self.incomingByte = ord(self.incomingByte)
				if self.incomingByte == 40:
					print("Recieved HELLO")
					self.packet_type = 1 
					self.CurrMode = 7
				elif self.incomingByte == 41:
					print("Recieved ACK")
					self.packet_type = 2
					self.CurrMode = 3
				elif self.incomingByte == 42:
					print("Recieved NACK")
					self.packet_type = 3
					self.CurrMode = 3
				elif self.incomingByte == 43:
					print("Recieved PROBE")
					self.packet_type = 4
					self.CurrMode = 3
				elif self.incomingByte == 44:
					print("Recieved REQ")
					self.packet_type = 5
					self.CurrMode = 3
				elif self.incomingByte == 45:
					print("Recieved DATA")
					self.packet_type = 6
					self.CurrMode = 3
				else:
					self.CurrMode = 8
					print("CORRUPT")
				
			elif self.CurrMode == 3 :
				self.incomingByte = ord(self.incomingByte)
			
				print("Payload_seq")
				print("expected: " + str(self.packet_seq_RX) + " actual: " + str(self.incomingByte))
				if self.packet_seq_RX != self.incomingByte:
					self.CurrMode = 8
					print("CORRUPT")
				else: 
					self.CurrMode = 4
					if self.packet_seq_RX == 48:
						self.packet_seq_RX = 49
					else: 
						self.packet_seq_RX = 48
			elif self.CurrMode == 4 :
				self.incomingByte = ord(self.incomingByte)
				component_ID = self.incomingByte
				print("component_id")
				if self.incomingByte >0 and self.incomingByte <41: 
					self.CurrMode = 5 
				else:
					self.CurrMode = 8
					print("CORRUPT")
			
			elif self.CurrMode == 5 :
				self.incomingByte = ord(self.incomingByte)
				self.incomingByte = int(self.incomingByte)
				
				print("payload")
				if self.dataIndex > -1: 
					self.data = self.data + self.incomingByte
					self.dataIndex = self.dataIndex-1 
					if self.dataIndex == 0:
						self.data = 0
						self.dataIndex = 8
						self.CurrMode = 6
		
			elif self.CurrMode == 6 :
				self.incomingByte = ord(self.incomingByte)
				print("crc")
				print self.incomingByte
				if self.incomingByte == 48: 
					self.CurrMode = 7 
					self.crcData = self.incomingByte
				else:
					self.CurrMode = 8 
					print("CORRUPT")

			elif self.CurrMode == 7:
				
				self.incomingByte = ord(self.incomingByte)
				print("Terminate")
				if self.incomingByte != 62 :
					self.CurrMode = 8
					print("CORRUPT")
					self.readStatus = False
				else:
					print("Successfully")
					self.CurrMode = 0
					self._buffer.append(str(self.component_ID) + '~' + str(self.data))
					# format of string : component_ID~data
					if len(self._buffer) % PiComms.SAMPLES_PER_PACKET == 0:
						self.forward_data()
					print(self.data)
					print(self.crcData)
					self.readStatus = False
					if self.packet_type ==1 or self.packet_type ==6:
						self.handling_packets()
			elif self.CurrMode == 8:
				print("Handling Corrupt Packet")
				self.CurrMode = 0
				self.readStatus = False

	def forward_data(self):
		datastream = ','.join(self._buffer)
		os.write(self.pipe_out, datastream)
		os.kill(int(self.pid), signal.SIGUSR1) # Raise SIGUSR1 signal
		self._buffer = []

	def send(self, packet_type_S, component_ID_S, data_S): 
		# global packet_seq_TX
		# global packet_type_TX
		# global component_ID_TX
		# global data_TX

		#Storing previous packet so it will not be overwritten
		self.packet_type_TX = packet_type_S
		self.component_ID_TX = component_ID_S
		self.data_TX = data_S
		print("Sending ACK Packet")
		self.ser.write("<")
		self.ser.write(chr(packet_type_S)) #41
		self.ser.write(chr(self.packet_seq_TX)) #0/1
		self.ser.write(chr(component_ID_S)) #12
		self.ser.write(self.convert(data_S)) #277
		self.ser.write("1")
		self.ser.write(">")
		#protected_flag = 1 

	def handling_packets(self): 
		# global packet_type
		# global packet_seq_TX
		# global packet_type_TX
		# global component_ID
		# global data_TX

		if self.packet_type == 1: #(HELLO RECEIVED) send hello back
			print "hello from the other side"
			#if protected_flag = 0: 
			self.ser.write("<")
			self.ser.write("(") 
			self.ser.write(">")
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

		elif self.packet_type == 6: #(DATA RECEIVED) send ack back with next pkt_seq
			#if protected_flag == 0:
			self.send(41, self.component_ID_TX, self.data_TX)
			self.packet_seq_TX = not self.packet_seq_TX
			#else:
			#	queueData = {'p_type': 41, 'com_id' : component_ID_TX , 'p_data' : data_TX}
			#	q.push(queueData, 1) 

	def txCRC(self):
		# global packet_type
		# global packet_seq_TX
		# global component_id
		# global data
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
	def xor(self, a, b):
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
	def mod2div(self, divident, divisor):

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
	def encodeData(self, data, key):

		l_key = len(key)

		# Appends n-1 zeroes at end of data
		appended_data = data + '0'*(l_key-1)
		remainder = self.mod2div(appended_data, key)

		# Append remainder in the original data
		codeword = data + remainder
		print("Remainder:")
		print(remainder)
		print("Encoded Data (Data + Remainder Appended):")
		print(codeword)

def main():
	comms = PiComms()
	while True:

		#if createQueue: 
		#	q = PriorityQueue() 
		#	createQueue = 0 
		#How to create this queue outside? 

		comms.read()

		#if protected_flag == 0: 
		#	toSend = q.pop() 
		#	if toSend.get('p_type') == 40:   #Special case for re-sending HELLO packet 
		#		ser.write("<")
		#		ser.write("(") 
		#		ser.write(">")
		#		protected_flag = 1 
		#	else: 
		#		send(toSend.get('p_type'), toSend.get('com_id'), toSend.get('p_data'))

if __name__ == "__main__":
	main()
