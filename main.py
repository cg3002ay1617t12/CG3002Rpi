from path_finder import PathFinder
from step_detection import StepDetector, counter
import os, signal, sys, subprocess, shlex, time
from fsm import *

# Global variables
EVENT_PIPE = '/Users/Jerry/CG3002Rpi/event_pipe'
DATA_PIPE  = '/Users/Jerry/CG3002Rpi/data_pipe'

def transition_handler(signum, frame, *args, **kwargs):
	""" Asynchronous event handler to trigger state transitions"""
	try:
		app = frame.f_globals['app']
	except KeyError as e:
		app = frame.f_locals['self']
	event = app.event_pipe.readline()
	transition = Transitions.recognize_input(event)
	print transition
	try:
		app.state = State.transitions[app.state][transition]
	except KeyError as e:
		pass

class App(object):
	def __init__(self):
		signal.signal(signal.SIGUSR1, transition_handler)
		self.pid = os.getpid()
		fpid = open('./pid', 'w')
		fpid.write(str(self.pid))
		fpid.close()
		
		# cmd = "python keyboard_sim.py"
		# self.child_process = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE) # Connect stdin of child_process to stdin of this process
		self.master = True
		self.state = State.START
		pipe_desc = os.open(DATA_PIPE, os.O_RDONLY)
		self.data_pipe = os.fdopen(pipe_desc)
		pipe_desc = os.open(EVENT_PIPE, os.O_RDWR)
		self.event_pipe = os.fdopen(pipe_desc, 'w+')
		
		# Init submodules
		self.PathFinder = PathFinder()
		self.StepDetector = counter
		self.StepDetector.run()
		
		# Transit to READY state
		self.event_pipe.write("SW_READY\r\n")
		os.kill(self.pid, signal.SIGUSR1)

	def run(self):
		while True:
			if self.state is State.END:
				break
			elif self.state is State.READY:
				# Do something, can be blocking or non-blocking
				print(self.state)
				time.sleep(5)
				pass
			elif self.state is State.NAVIGATING:
				# Do something, can be blocking or non-blocking
				print(self.state)
				time.sleep(5)
				pass
			elif self.state is State.REACHED:
				# Do something, can be blocking or non-blocking
				print(self.state)
				time.sleep(5)
				pass
			elif self.state is State.RESET:
				# Do something, can be blocking or non-blocking
				print(self.state)
				time.sleep(5)
				pass
			else:
				pass
		# Clean up system resources, close files and pipes, delete temp files
		# self.child_process.terminate()
		sys.exit(1)

def main():
	""" Main program of the Finite State Machine"""
	app = App()
	app.run()

if __name__ == "__main__":
	main()