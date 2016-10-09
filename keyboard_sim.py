import os, sys, signal, json
from fsm import *

ENV                = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
EVENT_PIPE         = ENV["EVENT_PIPE"]
PID                = ENV["PID_FILE"]

if not os.path.exists(EVENT_PIPE):
	os.mkfifo(EVENT_PIPE)

pipe_out = os.open(EVENT_PIPE, os.O_WRONLY)
fpid     = open(PID, 'r')
pid      = fpid.read()
while True:
	user_input = raw_input()
	os.write(pipe_out, user_input + "\r\n")
	os.kill(int(pid), signal.SIGUSR2) # Raise SIGUSR2 signal
