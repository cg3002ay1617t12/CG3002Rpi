import serial, struct, time, heapq, binascii, os, signal, sys, platform, json
from threading import Thread
from audio import AudioQueue

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

	DATA_PIPE          = './data_pipe'
	BAUD               = 115200
	SERIAL_ADDRESS_MAC = '/dev/cu.usbmodem1411'
	SERIAL_ADDRESS_RPI = '/dev/ttyAMA0'
	SAMPLES_PER_PACKET = 25
	CRC_POLY           = "100000111"

	def __init__(self):
		self.platform_               = platform.platform()
		self.ENV                     = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
		self.pq                      = PriorityQueue()
		self.aq                      = AudioQueue()
		for i in range(1):
			t = Thread(target=self.aq.run)
			t.daemon = True
			t.start()
		self.curr_mode               = 0
		self.packet_type             = 0 #ACK or HELLO or DATA 
		self.component_id            = 0
		if self.platform_            == "Linux-4.4.13-v6+-armv6l-with-debian-8.0":
			self.ser                     = serial.Serial(port =PiComms.SERIAL_ADDRESS_RPI, baudrate = PiComms.BAUD, timeout = 3)
		else:
			self.ser                     = serial.Serial(port =PiComms.SERIAL_ADDRESS_MAC, baudrate = PiComms.BAUD, timeout = 3)
		self.data                    = "" #Stores the payload for DATA packet 
		self.data_index              = -1 
		self.payload_length          = 0 
		self.incoming_byte           = 0 
		self.crc_data                = 0 
		self.crc_index               = 2 
		self.read_status             = False
		self.payload_final           = 0 
		self.crc_final               = 0
		self._buffer = {
			1: [],
			2: [],
			3: []
		}

		if not os.path.exists(PiComms.DATA_PIPE):
			os.mkfifo(PiComms.DATA_PIPE)

		# Write my pid
		fpid = open('./serial_pid', 'w')
		fpid.write(str(os.getpid()))
		fpid.close()

		# Open data pipe
		self.pipe_out = os.open(PiComms.DATA_PIPE, os.O_WRONLY)
		fpid          = open('./pid', 'r')
		self.pid      = fpid.read()
		fpid.close()

	def convert(self, number):
		count = 8
		to_send = [] 
		while (count > 0):
			count = count - 1
			if number>=255:
				number = number - 255
				to_send.append(struct.pack('!B', 255))
			else: 
				to_send.append(struct.pack('!B', number))
				number = 0
		data_string = ''.join(to_send)
		return data_string
		
	def read(self):
		# if self.ser.inWaiting()>0:
		self.read_status = True
		try:
			self.incoming_byte = self.ser.read()
			# print(ord(self.incoming_byte))
		except serial.SerialException as e:
			print e
			print("Reopening serial port...")
			while True:
				try:
					if self.platform_ == "Linux-4.4.13-v6+-armv6l-with-debian-8.0":
						self.ser.close()
						self.ser = serial.Serial(port =PiComms.SERIAL_ADDRESS_RPI, baudrate = PiComms.BAUD, timeout = 3)
					else:
						self.ser.close()
						self.ser = serial.Serial(port =PiComms.SERIAL_ADDRESS_MAC, baudrate = PiComms.BAUD, timeout = 3)
					break
				except Exception as e:
					time.sleep(5)
					pass
		except Exception as e:
			print("Terminated serial connection")
			sys.exit(1)
		try:
			# print("MODE: %d" % self.curr_mode)
			if self.curr_mode == 0: 
				self.incoming_byte = ord(self.incoming_byte)
				if self.incoming_byte == 60:
					self.curr_mode = 1
					# print("Received Start")

			elif self.curr_mode == 1:
				self.incoming_byte = ord(self.incoming_byte)
				if self.incoming_byte == 49:
					# print("Received HELLO")
					self.packet_type = 1 
					self.curr_mode = 7
				elif self.incoming_byte == 51:
					# print("Received ACK")
					self.packet_type = 2
					self.curr_mode = 7
				elif self.incoming_byte == 50:
					# print("Received DATA")
					self.packet_type = 6
					self.curr_mode = 2
				else:
					self.curr_mode = 8
					print("CORRUPT")
		
			elif self.curr_mode == 2 :
				self.incoming_byte = ord(self.incoming_byte)
				self.component_id = self.incoming_byte
				# print("receiving component_id")
				# print(self.component_id)
				if self.incoming_byte >0 and self.incoming_byte <42: 
					self.curr_mode = 3 
				else:
					self.curr_mode = 8
					print("CORRUPT")

			elif self.curr_mode == 3 :
				self.incoming_byte = ord(self.incoming_byte)
				self.payload_length = self.incoming_byte
				# print("receiving payload length")
				# print(self.payload_length)
				if self.incoming_byte >-1 and self.incoming_byte <58: 
					self.curr_mode = 5 
					self.data_index = self.payload_length
				else:
					self.curr_mode = 8
					print("CORRUPT")
			
			elif self.curr_mode == 5 :
				# print("receiving payload")
				if self.data_index > -1: 
					self.data = self.data + self.incoming_byte
					self.data_index = self.data_index-1 
					if self.data_index == 0:
						self.payload_final = self.data
						self.data = ""
						self.data_index = -1
						self.curr_mode = 6
		
			elif self.curr_mode == 6 :
				self.incoming_byte = ord(self.incoming_byte)
				# print("receiving crc")
				# print self.incoming_byte
				if self.crc_index >0 and self.incoming_byte == 49: 
					self.crc_data = self.crc_data + self.incoming_byte
					self.crc_index = self.crc_index - 1 
					if self.crc_index == 0:  
						self.crc_final = self.crc_data
						self.crc_data = 0
						self.crc_index = 2
						self.curr_mode = 7
				else:
					self.curr_mode = 8 
					print("CORRUPT")

			elif self.curr_mode == 7:
				self.incoming_byte = ord(self.incoming_byte)
				# print("Terminate")
				if self.incoming_byte != 62 :
					self.curr_mode = 8
					print("CORRUPT")
					self.read_status = False
				else:
					# print("Successfully")
					self.curr_mode = 0
					if self.packet_type ==6: 
						self.distribute_data()
					# Format of string : component_id~data
					# print ("String sent to buffer:") 
					# print(self.component_id)
					# print("~")
					# print(str(self.payload_final)),
					if self.packet_type ==1 or self.packet_type ==6:
						self.handling_packets()
					self.read_status = False

			elif self.curr_mode == 8:
				print("Handling Corrupt Packet")
				self.curr_mode = 0
				self.read_status = False
		except TypeError as e:
			# Most likely is ord() expected a character, but a string of length 0 found, arduino wiring might be loose
			self.aq.tts("ERROR connecting with Arduino... fix wires and press reset when ready!")
			print("[ERROR] Check connection with Arduino... Reset when ready")
		except Exception as e:
			print(e)

	def distribute_data(self):
		self._buffer[self.component_id].append(str(self.component_id) + '~' + str(self.clean_data(self.payload_final)) + '\r\n')
		self.forward_data()

	def forward_data(self):
		if len(self._buffer[self.component_id]) > 0 and len(self._buffer[self.component_id]) % PiComms.SAMPLES_PER_PACKET == 0:
			datastream = ''.join(self._buffer[self.component_id])
			os.write(self.pipe_out, datastream)
			os.kill(int(self.pid), signal.SIGUSR1) # Raise SIGUSR1 signal
			self._buffer[self.component_id] = []

	def handling_packets(self): 
		if self.packet_type == 1: #(HELLO RECEIVED) send hello back
			# print ("Sending HELLO Packet")
			self.ser.write("<1>")
			self.ser.flush()

		elif self.packet_type == 6: #(DATA RECEIVED) send ack back with next pkt_seq
			# print("Sending ACK Packet")
			self.ser.write("<3>")
			self.ser.flush()

	def clean_data(self, data): 
		values = data.strip('\0').strip('\r\n').strip() # Remove the insidious NULL character that dstrtof inserts sneakily
		return values

	def tx_crc(self):
		to_be_divided = []
		to_be_divided.append(format(60, "08b")) #START
		to_be_divided.append(format(11, "08b")) #PACKET_TYPE
		to_be_divided.append(format(22, "08b")) #PACKET_SEQ
		to_be_divided.append(format(44, "08b")) #COMPONENT_ID
		to_be_divided.append(format(65, "064b")) #DATA
		to_be_divided.append(format(0, "08b")) #PAD 8 ZEROS
		divided_string = ''.join(to_be_divided)
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
	def mod2_div(self, divident, divisor):

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

		check_word = tmp
		return check_word

	# Function used at the sender side to encode
	# data by appending remainder of modular divison
	# at the end of data.
	def encode_data(self, data, key):

		l_key = len(key)

		# Appends n-1 zeroes at end of data
		appended_data = data + '0'*(l_key-1)
		remainder = self.mod2_div(appended_data, key)

		# Append remainder in the original data
		code_word = data + remainder
		# print("Remainder:")
		# print(remainder)
		# print("Encoded Data (Data + Remainder Appended):")
		# print(code_word)

	@classmethod
	def signal_handler(cls, signum, frame):
		print("PiComms terminated connection to main")
		sys.exit(1)

def main():
	signal.signal(signal.SIGUSR1, PiComms.signal_handler)
	comms = PiComms()
	while True:
		comms.read()

if __name__ == "__main__":
	main()
