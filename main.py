from path_finder import PathFinder
from step_detection import StepDetector
import os, signal, sys, subprocess, shlex, time, json, threading, platform
from fsm import *
from localization import *
from audio import tts
from threading import Thread

class App(object):
	EVENT_PIPE = './event_pipe'
	DATA_PIPE  = './data_pipe'
	INSTRUCTION_INTERVAL = 8
	
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
		self.instruction     = ""
		self.start           = time.time()
		self.platform_pi = ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", "Linux-4.4.13+-armv6l-with-debian-8.0"]
		# Init submodules
		if self.platform_ in self.platform_pi:
			plot = False
		else:
			plot = False
		self.PathFinder   = PathFinder(1, 1)
		self.StepDetector = StepDetector(plot=plot)
		self.Localization = Localization(x=0, y=0, north=self.PathFinder.get_angle_of_north(), plot=plot)
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
		except Exception as e:
			print("[MAIN] Environment file not found, using defaults instead")
		
	def setup_pipes(self):
		# Setting up IPC
		self.master = True
		self.state = State.START
		pipe_desc = os.open(App.DATA_PIPE, os.O_RDONLY)
		print("[MAIN] Starting data pipe...listening for serial comms...")
		self.data_pipe = os.fdopen(pipe_desc)
		print("[MAIN] Serial comms connected!")
		pipe_desc = os.open(App.EVENT_PIPE, os.O_RDWR)
		print("[MAIN] Starting event pipe...listening for keystrokes...")
		self.event_pipe = os.fdopen(pipe_desc, 'w+')
		print("[MAIN] Keypad connected!")
		fpid = open('./serial_pid', 'r')
		app.serial_pid = fpid.read()
		fpid.close()
		fpid = open('./keypad_pid', 'r')
		app.keypad_pid = fpid.read()
		fpid.close()

	def register_handler(self):
		signal.signal(signal.SIGUSR2, transition_handler)
		signal.signal(signal.SIGUSR1, serial_handler)

	def issue_instruction(self):
		""" Only issue instruction after interval"""
		tts(self.instruction)
		self.instruction = ""

	def build_instruction(self, instr, placeholders=()):
		self.instruction += instr % placeholders

	def clear_instruction(self):
		self.instruction = ""

	def update_steps(self):
		if self.transition is Transitions.KEY_INCR:
			self.StepDetector.incr_step()
			self.Localization.incr_step()
		elif self.transition is Transitions.KEY_DECR:
			self.StepDetector.decr_step()
			self.Localization.decr_step()
		else:
			pass

	def get_instruction(self):
		angle = self.PathFinder.get_angle_to_next_node()
		if self.transition in [Transitions.KEY_GET_INSTR, Transitions.KEY_DECR, Transitions.KEY_INCR]:
			reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, angle)
			if reached:
				self.curr_reached_node = self.PathFinder.get_audio_reached(reached_node)
				self.build_instruction(self.curr_reached_node)
			else:
				self.build_instruction(self.PathFinder.get_audio_next_instruction())
		else:
			pass
		self.issue_instruction()
		self.clear_instruction()

	def run_once_on_transition(self, userinput):
		""" Run once upon transition to new state"""
		if self.state is State.END:
			tts("Shutting down.")
			pass
		elif self.state is State.ACCEPT_BUILDING:
			# tts("Please enter building")
			pass
		elif self.state is State.ACCEPT_LEVEL:
			# tts("Please enter level")
			try:
				self.building = int(userinput)
			except Exception as e:
				print e
			pass
		elif self.state is State.ACCEPT_START:
			# tts("Please enter start node")
			try:
				self.level = int(userinput)
				self.PathFinder = PathFinder(building=self.building, level=self.level)
			except ValueError as e:
				print("[MAIN] Error! Wrong building and level entered")
				tts("Please enter a valid building and level")
			except Exception as e:
				print(e)
			pass
		elif self.state is State.ACCEPT_END:
			# tts("Please enter end destination")
			try:
				self.curr_start_node = int(userinput)
				print '[MAIN] AEND userinput ' + str(userinput)
				print '[MAIN] AEND self.curr_start_node ' + str(self.curr_start_node)
			except Exception as e:
				print e
			(x, y)  = self.PathFinder.get_coordinates_from_node(self.curr_start_node)
			if x is None and y is None:
				print("[MAIN] Error! Invalid start node given, please try again")
				tts("Error, invalid start, please enter again")
			else:
				bearing = self.Localization.stabilized_bearing
				self.PathFinder.update_coordinate(x, y, bearing)
				self.Localization.update_coordinates(x, y)
				self.update_steps()
			pass
		elif self.state is State.NAVIGATING:
			try:
				self.curr_end_node = int(userinput)
			except Exception as e:
				pass
			if self.transition is Transitions.KEY_NODE:
				print 'NAVI self.curr_start_node ' + str(self.curr_start_node)
				self.PathFinder.update_source_and_target(self.curr_start_node, self.curr_end_node)
				print("[MAIN] Source : %d, Dest: %d" % (self.curr_start_node, self.curr_end_node))
				print("[MAIN] Current location: %.2f, %.2f, %.2f" % (self.PathFinder.get_x_coordinate(), self.PathFinder.get_y_coordinate(), self.Localization.stabilized_bearing))
				bearing = self.Localization.stabilized_bearing
				self.PathFinder.update_coordinate(x, y, bearing)
			self.update_steps()
			self.get_instruction()
		elif self.state is State.REACHED:
			# self.curr_reached_node = self.PathFinder.get_audio_reached(self.curr_end_node)
			self.update_steps()
			self.get_instruction()
			pass
		elif self.state is State.RESET:
			tts("Resetting. ")
			self.StepDetector.reset_step()
			self.Localization.reset()
			pass
		else:
			pass
		if self.transition is Transitions.KEY_GET_PREV:
			tts("Previous " + str(self.PathFinder.get_prev_visited_node()))
		elif self.transition is Transitions.KEY_REACHED_NODE:
			# When user press 6
			new_coord = self.PathFinder.get_next_coordinates()
			if new_coord[0] is not None and new_coord[1] is not None:
				self.Localization.update_coordinates(new_coord[0], new_coord[1])
				self.PathFinder.update_coordinate(new_coord[0], new_coord[1], self.Localization.stabilized_bearing)
			else:
				print("[MAIN] Error! Invalid new coordinates for reached node")
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
				elif self.state is State.ACCEPT_BUILDING:
					# self.Localization.run(self.StepDetector.curr_steps)
					pass
				elif self.state is State.ACCEPT_LEVEL:
					# self.Localization.run(self.StepDetector.curr_steps)
					pass
				elif self.state is State.ACCEPT_START:
					# Do something, make sure its non-blocking
					# self.Localization.run(self.StepDetector.curr_steps)
					# Cannot do anything because we do not know where the user is
					pass
				elif self.state is State.ACCEPT_END:
					# Do something, make sure its non-blocking
					# self.Localization.run(self.StepDetector.curr_steps)
					# Wait for user to key in destination
					pass
				elif self.state is State.NAVIGATING:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					angle = self.PathFinder.get_angle_to_next_node()
					self.Localization.run(self.StepDetector.curr_steps, angle=angle)
					if self.StepDetector.curr_steps > 0:
						self.build_instruction("Step")
					if time.time() - self.start > 2:
						print("[MAIN] Heading : %.2f" % (self.Localization.stabilized_bearing))
						self.start = time.time()
					reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, angle)
					if reached:
						self.curr_reached_node = self.PathFinder.get_audio_reached(reached_node)
						self.build_instruction(self.curr_reached_node)
						(x, y) = self.PathFinder.get_coordinates_from_node(reached_node)
						self.Localization.update_coordinates(x, y)
						self.StepDetector.curr_steps = 0
						# Transit to REACHED state
						self.event_pipe.write("CHECKPOINT_REACHED\r\n")
						os.kill(self.pid, signal.SIGUSR2)
					else:
						self.build_instruction(self.PathFinder.get_audio_next_instruction())
					if self.StepDetector.curr_steps > 0:
						self.issue_instruction()
					self.StepDetector.curr_steps = 0
					self.clear_instruction()
					pass
				elif self.state is State.REACHED:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					angle = self.PathFinder.get_angle_to_next_node()
					self.Localization.run(self.StepDetector.curr_steps, angle=angle)
					if self.StepDetector.curr_steps > 0:
						self.build_instruction("Step. ")
					if time.time() - self.start > 2:
						self.start = time.time()
						print("[MAIN] Heading is : %.2f " % (self.Localization.stabilized_bearing))	
					reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, angle)
					if reached:
						self.curr_reached_node = self.PathFinder.get_audio_reached(reached_node)
						self.build_instruction(self.PathFinder.get_audio_reached(reached_node))
					else:
						self.build_instruction("Arrived. ")
						self.build_instruction(self.curr_reached_node)
						self.build_instruction(self.PathFinder.get_audio_next_instruction())
					if (self.StepDetector.curr_steps > 0):
						self.issue_instruction()
					self.StepDetector.curr_steps = 0
					self.clear_instruction()
					pass
				elif self.state is State.RESET:
					# Do something, make sure its non-blocking
					self.StepDetector.run()
					angle = self.PathFinder.get_angle_to_next_node()
					self.Localization.run(self.StepDetector.curr_steps, angle=angle)
					if (self.StepDetector.curr_steps > 0):
						self.build_instruction("Step. ")	
					reached, reached_node = self.PathFinder.update_coordinate(self.Localization.x, self.Localization.y, angle)
					if reached:
						self.curr_reached_node = self.PathFinder.get_audio_reached(reached_node)
						self.build_instruction(self.PathFinder.get_audio_reached(reached_node))
					else:
						self.build_instruction(self.PathFinder.get_audio_next_instruction())
					if self.StepDetector.curr_steps > 0:
						self.issue_instruction()
					self.StepDetector.curr_steps = 0
					self.clear_instruction()
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
		print("[MAIN] Killed serial process %s" % app.serial_pid)
		tts("Error...timeout on serial data. Check Arduino connection and reset when ready")
	except Exception as e:
		pass # Process may have terminated already
	connect_picomms(platform=app.platform_)

def transition_handler(signum, frame, *args, **kwargs):
	""" Asynchronous event handler to trigger state transitions"""
	global app
	event = app.event_pipe.readline()
	(transition, userinput) = Transitions.recognize_input(event)
	print("[MAIN] " + str(transition))
	try:
		app.state      = State.transitions[app.state][transition]
		app.transit    = True
		app.userinput  = userinput
		app.transition = transition
		print("[MAIN] " + str(app.state))
	except KeyError as e:
		pass

def serial_handler(signum, frame, *args, **kwargs):
	""" Handles all incoming sensor data and distribute to the relevant submodules"""
	global app
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
	if app.platform_ in app.platform_pi:
		map(process_laptop, buffer_)
	else:
		map(process_laptop, buffer_)
		# map(process_laptop, buffer_)
	if time.time() - app.start > 5:
		print("[MAIN] Incoming serial data from Arduino")
		app.start = time.time()
	app.StepDetector.new_data = True
	app.Localization.new_data = True

def connect_keypad(platform=None):
	print("[MAIN] Connecting with Keypad...")
	if platform in ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", "Linux-4.4.13+-armv6l-with-debian-8.0"] : # Raspberry Pi
		cmd     = "python keypad.py"
	elif platform in ["Darwin-15.2.0-x86_64-i386-64bit", "Linux-3.4.0+-x86_64-with-Ubuntu-14.04-trusty"]:
		cmd     = "python keyboard_sim.py" # Mac, Windows, Ubuntu with connected keyboard
	else:
		cmd     = "python keyboard_sim.py" # Mac, Windows, Ubuntu with connected keyboard
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("[MAIN] Connection established!")
	return process

def connect_picomms(platform=None):
	print("[MAIN] Connecting with Arduino...")
	if platform in ["Linux-4.4.13-v6+-armv6l-with-debian-8.0", "Linux-4.4.13+-armv6l-with-debian-8.0"] :
		# cmd     = "python pi_comms.py"
		cmd     = "python serial_input.py"
	elif platform == "Darwin-15.2.0-x86_64-i386-64bit" or platform == "Linux-3.4.0+-x86_64-with-Ubuntu-14.04-trusty":
		# cmd     = "python serial_input.py"
		cmd     = "python pi_comms.py"
	else:
		cmd     = "python serial_input.py"
	args    = shlex.split(cmd)
	process = subprocess.Popen(args)
	print("[MAIN] Connection established!")
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
