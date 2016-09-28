from path_finder import PathFinder
from vhf import LocalPathFinder
from step_detection import StepDetector, counter, serial_handler
import os, signal, sys, subprocess, shlex, time
from fsm import *

# Global variables
EVENT_PIPE = './event_pipe'
DATA_PIPE  = './data_pipe'

class App(object):
	def __init__(self):
		self.pid = os.getpid()
		fpid = open('./pid', 'w')
		fpid.write(str(self.pid))
		fpid.close()
		
		# cmd = "python keyboard_sim.py"
		# self.child_process = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE) # Connect stdin of child_process to stdin of this process
		self.master = True
		self.state = State.START
		pipe_desc = os.open(DATA_PIPE, os.O_RDONLY)
		print("Starting data pipe...listening for serial comms...")
		self.data_pipe = os.fdopen(pipe_desc)
		print("Serial comms connected!")
		pipe_desc = os.open(EVENT_PIPE, os.O_RDWR)
		print("Starting event pipe...listening for keystrokes...")
		self.event_pipe = os.fdopen(pipe_desc, 'w+')
		print("Keypad connected!")
		
		# Init submodules
		self.PathFinder = PathFinder()
		self.StepDetector = counter
		self.LPF = LocalPathFinder(mode='demo')

	def register_handler(self):
		signal.signal(signal.SIGUSR2, transition_handler)
		signal.signal(signal.SIGUSR1, serial_handler)

	def run(self):
		while True:
			if self.state is State.END:
				break
			elif self.state is State.READY:
				# Do something, make sure its interruptible and non-blocking
				self.StepDetector.run()
				self.LPF.run(plot=False)
				pass
			elif self.state is State.NAVIGATING:
				# Do something, make sure its interruptible and non-blocking
				self.StepDetector.run()
				self.LPF.run(plot=False)
				pass
			elif self.state is State.REACHED:
				# Do something, make sure its interruptible and non-blocking
				self.StepDetector.run()
				self.LPF.run(plot=False)
				pass
			elif self.state is State.RESET:
				# Do something, make sure its interruptible and non-blocking
				self.StepDetector.reset_step()
				self.StepDetector.run()
				self.LPF.run(plot=False)
				pass
			else:
				pass
		# Clean up system resources, close files and pipes, delete temp files
		# self.child_process.terminate()
		sys.exit(1)

app = App()
def transition_handler(signum, frame, *args, **kwargs):
	""" Asynchronous event handler to trigger state transitions"""
	global app
	event = app.event_pipe.readline()
	transition = Transitions.recognize_input(event)
	print transition
	try:
		app.state = State.transitions[app.state][transition]
		print(app.state)
	except KeyError as e:
		pass

def main():
	""" Main program of the Finite State Machine"""
	global app
	app.register_handler()
	# Transit to READY state
	app.event_pipe.write("SW_READY\r\n")
	os.kill(app.pid, signal.SIGUSR2)
	app.run()

if __name__ == "__main__":
	main()
