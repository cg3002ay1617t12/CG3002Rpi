import os, sys, signal
from fsm import *

# DATA_PIPE          = '/Users/Jerry/CG3002Rpi/data_pipe'
EVENT_PIPE         = '/Users/Jerry/CG3002Rpi/event_pipe'

if not os.path.exists(EVENT_PIPE):
	os.mkfifo(EVENT_PIPE)

pipe_out = os.open(EVENT_PIPE, os.O_WRONLY)
fpid     = open('./pid', 'r')
pid      = fpid.read()
while True:
	user_input = raw_input()
	os.write(pipe_out, user_input + "\r\n")
	os.kill(int(pid), signal.SIGUSR2) # Raise SIGUSR2 signal
