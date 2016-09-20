import serial, os, sys, signal

PIPE               = '/Users/Jerry/CG3002Rpi/pipe'
BAUD               = 115400
SERIAL             = '/dev/cu.usbmodem1411'
SAMPLES_PER_PACKET = 25
if not os.path.exists(PIPE):
	os.mkfifo(PIPE)

pipe_out = os.open(PIPE, os.O_WRONLY)
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