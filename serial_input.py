import serial, os, sys, signal, json

ENV                = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
DATA_PIPE          = ENV["DATA_PIPE"]
EVENT_PIPE         = ENV["EVENT_PIPE"]
BAUD               = ENV["SERIAL_BAUD_RATE"]
# SERIAL             = ENV["SERIAL_ADDRESS_RPI"]
SERIAL             = ENV["SERIAL_ADDRESS_MAC"]
PID                = ENV["PID_FILE"]
SAMPLES_PER_PACKET = ENV["STEP_SAMPLES_PER_PACKET"]

if not os.path.exists(DATA_PIPE):
	os.mkfifo(DATA_PIPE)

pipe_out = os.open(DATA_PIPE, os.O_WRONLY)
fpid     = open(PID, 'r')
pid      = fpid.read()
ser      = serial.Serial(SERIAL, BAUD, timeout=1)
count    = 0
data     = []
os.write(pipe_out, '\r\n')
while True:
	try:
		datum = ser.readline()
		data.append(datum)   # read a '\n' terminated line
		count += 1
		if count % SAMPLES_PER_PACKET == 0:
			packet = ''.join(data)
			os.write(pipe_out, packet)
			os.kill(int(pid), signal.SIGUSR1) # Raise SIGUSR1 signal
			data = []
	except serial.SerialException as e:
		print e
