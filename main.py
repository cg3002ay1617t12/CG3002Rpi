from path_finder import PathFinder
from vhf import LocalPathFinder
from step_detection import StepDetector
import os, signal, sys, subprocess, shlex, time, json, threading
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
		# self.PathFinder   = PathFinder()
		self.StepDetector = StepDetector(plot=False)
		self.Localization = Localization(x=0, y=0, north=0, plot=True)
		# self.LPF = LocalPathFinder(mode='demo')

		# Init environment and user-defined variables
		try:
			self.ENV                           = json.loads(open(os.path.join(os.path.dirname(__file__), 'env.json')).read())
			StepDetector.SAMPLES_PER_PACKET    = self.ENV["STEP_SAMPLES_PER_PACKET"]
			StepDetector.SAMPLES_PER_WINDOW    = self.ENV["STEP_SAMPLES_PER_WINDOW"]
			StepDetector.INTERRUPTS_PER_WINDOW = StepDetector.SAMPLES_PER_WINDOW / StepDetector.SAMPLES_PER_PACKET
			self.StepDetector.THRES            = self.ENV["STEP_THRES"]
			self.Localization.stride           = self.ENV["STRIDE_LENGTH"]
			App.DATA_PIPE                      = self.ENV['DATA_PIPE']
			App.EVENT_PIPE                     = self.ENV['EVENT_PIPE']
			# print(self.env)
		except Exception as e:
			print("Environment file not found, using defaults instead")
		
	def setup_pipes(self):
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
		fpid = open('./serial_pid', 'r')
		app.serial_pid = fpid.read()
		fpid.close()
		fpid = open('./keypad_pid', 'r')
		app.keypad_pid = fpid.read()
		fpid.close()

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
			self.Localization.reset()
			pass
		else:
			pass

	def run(self):
		""" Run forever while in this state"""
		while True:
			try:
				if self.state is State.END:
					break
				elif self.state is State.READY:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					self.StepDetector.curr_steps = 0
					pass
				elif self.state is State.NAVIGATING:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					self.StepDetector.curr_steps = 0
					pass
				elif self.state is State.REACHED:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					self.StepDetector.curr_steps = 0
					pass
				elif self.state is State.RESET:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					self.StepDetector.curr_steps = 0
					pass
				else:
					pass
			except Exception as e:
				print(e)
		# Clean up system resources, close files and pipes, delete temp files
		os.kill(int(self.serial_pid), signal.SIGTERM)
		os.kill(int(self.keypad_pid), signal.SIGTERM)
		sys.exit(0)

app = App()
def timeout_handler():
	global app
	try:
		os.kill(int(app.serial_pid), signal.SIGUSR1)
		print("triggered! %s" % app.serial_pid)
	except Exception as e:
		pass # Process may have terminated already
	connect_picomms()

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

def serial_handler(signum, frame, *args, **kwargs):
	""" Handles all incoming sensor data and distribute to the relevant submodules"""
	global app
	def process(datum):
		try:
			(x,y,z,a,b,c,d) = map(lambda x: x.strip('\r\n'), datum.split(','))
			app.StepDetector.ax.append(float(x))
			app.StepDetector.ay.append(float(y))
			app.StepDetector.az.append(float(z))
			app.Localization.heading.append(float(d))
			app.Localization.rotate_x.append(float(a))
			app.Localization.rotate_y.append(float(b))
			app.Localization.rotate_z.append(float(c))
		except ValueError as e:
			print e
	# terminate process in timeout seconds
	timeout    = 2 # seconds
	timer      = threading.Timer(timeout, timeout_handler)
	timer.start()
	line_count = StepDetector.SAMPLES_PER_PACKET
	buffer_    = []
	while line_count > 0:
		data = app.data_pipe.readline()
		buffer_.append(data)
		line_count -= 1
	timer.cancel()
	map(process, buffer_)
	app.StepDetector.new_data = True
	app.Localization.new_data = True

def connect_keypad():
	print("Connecting with Keypad...")
	cmd     = "python keyboard_sim.py"
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("Connection established!")
	return process

def connect_picomms():
	print("Connecting with PiComms...")
	cmd     = "python serial_input.py"
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("Connection established!")
	return process

def main():
	""" Main program of the Finite State Machine"""
	global app
	if os.fork() == 0:
		# Child processes
		signal.signal(signal.SIGALRM, timeout_handler)
		p1 = connect_picomms()
		p2 = connect_keypad()
		fpid = open('./keypad_pid', 'w')
		fpid.write(str(p2.pid))
		fpid.close()
		os._exit(0)
	else:
		# Parent process
		app.register_handler()
		app.setup_pipes()
		# Transit to READY state
		app.event_pipe.write("SW_READY\r\n")
		os.kill(app.pid, signal.SIGUSR2)
		app.run()

if __name__ == "__main__":
	main()
