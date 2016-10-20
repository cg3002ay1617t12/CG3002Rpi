from path_finder import PathFinder
from step_detection import StepDetector
import os, signal, sys, subprocess, shlex, time, json, threading, platform
from fsm import *
from localization import *
from audio import AudioQueue
from threading import Thread

class App(object):
	EVENT_PIPE = './event_pipe'
	DATA_PIPE  = './data_pipe'
	INSTRUCTION_INTERVAL = 5
	
	def __init__(self):
		self.platform_ = platform.platform()
		self.pid = os.getpid()
		fpid = open('./pid', 'w')
		fpid.write(str(self.pid))
		fpid.close()
		
		self.curr_start_node = -1
		self.curr_end_node   = -1
		self.transit         = False
		self.userinput       = ''
		self.transition      = None
		self.start           = time.time()
		self.platform_pi = ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", "Linux-4.4.13+-armv6l-with-debian-8.0"]
		# Init submodules
		if self.platform_ in self.platform_pi:
			plot = False
		else:
			plot = False
		self.PathFinder   = PathFinder()
		self.StepDetector = StepDetector(plot=plot)
		self.Localization = Localization(x=0, y=0, north=self.PathFinder.get_angle_of_north(), plot=plot)
		self.aq           = AudioQueue()
		# Start audio queue workers
		for i in range(1):
			t = Thread(target=self.aq.run)
			t.daemon = True
			t.start()
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

	def issue_instruction(self, instr, placeholders=()):
		if (time.time() - self.start) > App.INSTRUCTION_INTERVAL:
			self.aq.tts(instr, placeholders)
			self.start = time.time()

	def wait_for_stable_heading(self):
		""" Wait for a stable heading from compass to init PathFinder"""
		while True:
			reading = self.Localization.get_stabilized_bearing()
			if reading > 0:
				return reading

	def update_steps(self):
		if self.transition is Transitions.KEY_INCR:
			self.StepDetector.incr_step()
			self.Localization.incr_step()
		elif self.transition is Transitions.KEY_DECR:
			self.StepDetector.decr_step()
			self.Localization.decr_step()
		else:
			pass

	def run_once_on_transition(self, userinput):
		""" Run once upon transition to new state"""
		if self.state is State.END:
			self.aq.tts("Shutting down now")
			pass
		elif self.state is State.ACCEPT_START:
			self.aq.tts("Please enter start node")
			pass
		elif self.state is State.ACCEPT_END:
			self.aq.tts("Please enter end destination")
			try:
				self.curr_start_node = int(userinput)
			except Exception as e:
				pass
			(x, y)  = self.PathFinder.get_coordinates_from_node(self.curr_start_node)
			bearing = self.Localization.stabilized_bearing
			self.PathFinder.update_coordinate(x, y, bearing)
			self.Localization.update_coordinates(x, y)
			self.update_steps()
			pass
		elif self.state is State.NAVIGATING:
			self.aq.tts("Entering navigation state")
			try:
				self.curr_end_node = int(userinput)
			except Exception as e:
				pass
			self.PathFinder.update_source_and_target(self.curr_start_node, self.curr_end_node)
			print("Source : %d, Dest: %d" % (self.curr_start_node, self.curr_end_node))
			print("Current location: %.2f, %.2f, %.2f" % (self.PathFinder.get_x_coordinate(), self.PathFinder.get_y_coordinate(), self.Localization.stabilized_bearing))
			self.update_steps()
			pass
		elif self.state is State.REACHED:
			self.aq.tts("You have arrived!")
			self.aq.tts(self.PathFinder.get_audio_reached(self.curr_end_node))
			self.update_steps()
			pass
		elif self.state is State.RESET:
			self.aq.tts("Resetting step counter and localization module")
			self.StepDetector.reset_step()
			self.Localization.reset()
			pass
		else:
			pass
		self.transit = False

	def run(self):
		""" Run forever and multiplex between the states """
		while True:
			if self.transit:
				self.run_once_on_transition(self.userinput)
			try:
				if self.state is State.END:
					break
				elif self.state is State.ACCEPT_START:
					# Do something, make sure its non-blocking
					self.Localization.run(self.StepDetector.curr_steps)
					# Cannot do anything because we do not know where the user is
					pass
				elif self.state is State.ACCEPT_END:
					# Do something, make sure its non-blocking
					self.Localization.run(self.StepDetector.curr_steps)
					# Wait for user to key in destination
					pass
				elif self.state is State.NAVIGATING:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					(reached, node) = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
					if reached:
						self.issue_instruction(self.PathFinder.get_audio_reached(node))
						# Transit to REACHED state
						self.event_pipe.write("CHECKPOINT_REACHED\r\n")
						os.kill(self.pid, signal.SIGUSR2)
					else:
						self.issue_instruction(self.PathFinder.get_audio_next_instruction())
					self.StepDetector.curr_steps = 0
					pass
				elif self.state is State.REACHED:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					(reached, node) = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
					if reached:
						self.issue_instruction(self.PathFinder.get_audio_reached(node))
					else:
						self.issue_instruction(self.PathFinder.get_audio_next_instruction())
					self.StepDetector.curr_steps = 0
					pass
				elif self.state is State.RESET:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					self.Localization.run(self.StepDetector.curr_steps)
					(reached, node) = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, self.Localization.stabilized_bearing)
					if reached:
						self.issue_instruction(self.PathFinder.get_audio_reached(node))
					else:
						self.issue_instruction(self.PathFinder.get_audio_next_instruction())
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
	connect_picomms(platform=app.platform_)

def transition_handler(signum, frame, *args, **kwargs):
	""" Asynchronous event handler to trigger state transitions"""
	global app
	event = app.event_pipe.readline()
	(transition, userinput) = Transitions.recognize_input(event)
	print transition
	try:
		app.state      = State.transitions[app.state][transition]
		app.transit    = True
		app.userinput  = userinput
		app.transition = transition
		print(app.state)
	except KeyError as e:
		pass

def serial_handler(signum, frame, *args, **kwargs):
	""" Handles all incoming sensor data and distribute to the relevant submodules"""
	global app
	print("Incoming serial data...")
	def process_rpi(datum):
		""" Run this if using the pi_comms protocol"""
		(component_id, readings) = datum.split('~')
		component_id = int(component_id)
		try:
			if component_id == 1:
				(a_x, a_y, a_z) = map(lambda x: x.strip('\0\r\n\t'), readings.split(','))
				app.StepDetector.ax.append(float(a_x))
				app.StepDetector.ay.append(float(a_y))
				app.StepDetector.az.append(float(a_z))
			if component_id == 2:
				heading = readings.strip('\r\n').strip('\0\n\r\t')
				app.Localization.heading.append(float(heading))
			if component_id == 3:
				(g_x, g_y, g_z) = map(lambda x: x.strip(' \0\r\n\t'), readings.split(','))
				app.Localization.rotate_x.append(float(g_x))
				app.Localization.rotate_y.append(float(g_y))
				app.Localization.rotate_z.append(float(g_z))
		except ValueError as e:
			print e
	
	def process_laptop(datum):
		""" Run this if not using the pi_comms protocol"""
		try:
			(x,y,z,a,b,c,d) = map(lambda x: x.strip('\r\n'), readings.split(','))
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
	if app.platform_ in app.platform_pi:
		map(process_rpi, buffer_)
	else:
		map(process_rpi, buffer_)
		# map(process_laptop, buffer_)
	app.StepDetector.new_data = True
	app.Localization.new_data = True

def connect_keypad(platform=None):
	print("Connecting with Keypad...")
	if platform in ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", "Linux-4.4.13+-armv6l-with-debian-8.0"] : # Raspberry Pi
		cmd     = "python keypad.py"
	elif platform in ["Darwin-15.2.0-x86_64-i386-64bit", "Linux-3.4.0+-x86_64-with-Ubuntu-14.04-trusty"]:
		cmd     = "python keyboard_sim.py" # Mac, Windows, Ubuntu with connected keyboard
	else:
		cmd     = "python keyboard_sim.py" # Mac, Windows, Ubuntu with connected keyboard
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("Connection established!")
	return process

def connect_picomms(platform=None):
	print("Connecting with Arduino...")
	if platform in ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", "Linux-4.4.13+-armv6l-with-debian-8.0"] :
		cmd     = "python pi_comms.py"
		# cmd     = "python serial_input.py"
	elif platform == "Darwin-15.2.0-x86_64-i386-64bit" or platform == "Linux-3.4.0+-x86_64-with-Ubuntu-14.04-trusty":
		# cmd     = "python serial_input.py"
		cmd     = "python pi_comms.py"
	else:
		cmd     = "python serial_input.py"
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("Connection established!")
	return process

def main():
	""" Main program of the Finite State Machine"""
	global app
	platform_ = platform.platform()
	if os.fork() == 0:
		# Child processes
		signal.signal(signal.SIGALRM, timeout_handler)
		p1 = connect_picomms(platform_)
		p2 = connect_keypad(platform_)
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
