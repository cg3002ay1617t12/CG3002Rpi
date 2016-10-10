from path_finder import PathFinder
from vhf import LocalPathFinder
from step_detection import StepDetector, counter, serial_handler
import os, signal, sys, subprocess, shlex, time, json
from fsm import *
from localization import *

class App(object):
	EVENT_PIPE = './event_pipe'
	DATA_PIPE  = './data_pipe'
	
	def __init__(self):
		self.pid = os.getpid()
		fpid = open('./pid', 'w')
		fpid.write(str(self.pid))
		fpid.close()
		
		# Init submodules
		self.PathFinder = PathFinder()
		self.StepDetector = counter
		# self.LPF = LocalPathFinder(mode='demo')

		# Init environment and user-defined variables
		try:
			self.ENV                           = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
			StepDetector.SAMPLES_PER_PACKET    = self.ENV["STEP_SAMPLES_PER_PACKET"]
			StepDetector.SAMPLES_PER_WINDOW    = self.ENV["STEP_SAMPLES_PER_WINDOW"]
			StepDetector.INTERRUPTS_PER_WINDOW = StepDetector.SAMPLES_PER_WINDOW / StepDetector.SAMPLES_PER_PACKET
			self.StepDetector.THRES            = self.ENV["STEP_THRES"]
			App.DATA_PIPE                      = self.ENV['DATA_PIPE']
			App.EVENT_PIPE                     = self.ENV['EVENT_PIPE']
			# print(self.env)
		except Exception as e:
			print("Environment file not found, using defaults instead")
		
		# Setting up IPC
		self.master = True
		self.state = State.START
		pipe_desc = os.open(App.DATA_PIPE, os.O_RDONLY)
		print("Starting data pipe...listening for serial comms...")
		self.data_pipe = os.fdopen(pipe_desc)
		print("Serial comms connected!")
		pipe_desc = os.open(App.EVENT_PIPE, os.O_RDWR)
		print("Starting event pipe...listening for keystrokes...")
		self.event_pipe = os.fdopen(pipe_desc, 'w+')
		print("Keypad connected!")

	def register_handler(self):
		signal.signal(signal.SIGUSR2, transition_handler)
		signal.signal(signal.SIGUSR1, serial_handler)

	def run_once_on_transition(self):
		""" Run once upon transition to this state"""
		if self.state is State.END:
			pass
		elif self.state is State.READY:
			pass
		elif self.state is State.NAVIGATING:
			pass
		elif self.state is State.REACHED:
			pass
		elif self.state is State.RESET:
			self.StepDetector.reset_step()
			pass
		else:
			pass

	def run(self):
		""" Run forever while in this state"""
		while True:
			if self.state is State.END:
				break
			elif self.state is State.READY:
				# Do something, make sure its non-blocking
				self.StepDetector.run()
				pass
			elif self.state is State.NAVIGATING:
				# Do something, make sure its non-blocking
				self.StepDetector.run()
				pass
			elif self.state is State.REACHED:
				# Do something, make sure its non-blocking
				self.StepDetector.run()
				pass
			elif self.state is State.RESET:
				# Do something, make sure its non-blocking
				self.StepDetector.run()
				pass
			else:
				pass
		# Clean up system resources, close files and pipes, delete temp files
		sys.exit(0)

app = App()
def transition_handler(signum, frame, *args, **kwargs):
	""" Asynchronous event handler to trigger state transitions"""
	global app
	event = app.event_pipe.readline()
	transition = Transitions.recognize_input(event)
	print transition
	try:
		app.state = State.transitions[app.state][transition]
		app.run_once_on_transition()
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
