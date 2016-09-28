import serial, os, sys, signal

#DATA_PIPE          = '/Users/Jerry/CG3002Rpi/data_pipe'
#EVENT_PIPE         = '/Users/Jerry/CG3002Rpi/event_pipe'
#BAUD               = 115400
#SERIAL             = '/dev/cu.usbmodem1411'
#SAMPLES_PER_PACKET = 25

DATA_PIPE          = './CG3002Rpi/data_pipe'
EVENT_PIPE         = './CG3002Rpi/event_pipe'
BAUD               = 115200
SERIAL             = '/dev/ttyAMA0'
SAMPLES_PER_PACKET = 25

if not os.path.exists(DATA_PIPE):
	os.mkfifo(DATA_PIPE)
# if not os.path.exists(EVENT_PIPE):
# 	os.mkfifo(EVENT_PIPE)

pipe_out = os.open(DATA_PIPE, os.O_WRONLY)
fpid     = open('./pid', 'r')
pid      = fpid.read()
ser      = serial.Serial(SERIAL, BAUD, timeout=1)
count    = 0
data     = []
while True:
	data.append(ser.readline())   # read a '\n' terminated line
	count += 1
	if count % SAMPLES_PER_PACKET == 0:
		packet = ''.join(data)
		os.write(pipe_out, packet)
		os.kill(int(pid), signal.SIGUSR1) # Raise SIGUSR1 signal
		data = []
